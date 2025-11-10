import os
import json
import threading
from datetime import datetime
from fastapi import FastAPI, Depends, Request, Response, HTTPException
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine, Column, Integer, Float, String, BigInteger, DateTime, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import paho.mqtt.client as mqtt
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST


class Settings(BaseSettings):
    # Database settings
    POSTGRESQL_HOST: str
    POSTGRESQL_PORT: str
    POSTGRESQL_USER: str
    POSTGRESQL_PASSWORD: str
    POSTGRESQL_DBNAME: str

    # MQTT settings
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883

    class Config:
        env_file = ".env"


settings = Settings()

# FastAPI Setup
app = FastAPI(
    title="Unified Solar Still Monitoring API",
    version="2.0.0",
    description="Supports both conventional and automated solar still systems"
)

# Database Setup
DATABASE_URL = f"postgresql+psycopg2://{settings.POSTGRESQL_USER}:{settings.POSTGRESQL_PASSWORD}@{settings.POSTGRESQL_HOST}:{settings.POSTGRESQL_PORT}/{settings.POSTGRESQL_DBNAME}"

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        print("✓ Database connection successful!")
except Exception as e:
    print(f"✗ Failed to connect to database: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Unified Database Model
class SolarStillData(Base):
    __tablename__ = "solar_still_data"

    id = Column(BigInteger, primary_key=True, index=True)

    # System identification
    system_type = Column(String, nullable=False, index=True)  # "conventional" or "automated"

    # Temperature data
    temperature = Column(Float, nullable=False)  # Average temperature
    temp1 = Column(Float, nullable=True)  # T1 (Thermistor 1)
    temp2 = Column(Float, nullable=True)  # T2 (Thermistor 2)
    temp3 = Column(Float, nullable=True)  # T3 (Thermistor 3)
    temp4 = Column(Float, nullable=True)  # T4 (Thermistor 4)
    temp5 = Column(Float, nullable=True)  # T5 (Thermistor 5)

    # Water level data
    water_depth_cm = Column(Float, nullable=False)
    water_raw_adc = Column(Integer, nullable=True)

    # Pump status (only for automated systems)
    pump_status = Column(String, nullable=True)  # "ON", "OFF", or null for conventional

    # Timestamps
    time_stamp = Column(String, nullable=True)  # ISO8601 from ESP32 RTC
    created_at = Column(DateTime, server_default=func.now(), index=True)


Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Input Models
class WaterLevelData(BaseModel):
    raw_adc: int
    depth_cm: float


class SolarStillDataIn(BaseModel):
    system_type: str  # "conventional" or "automated"
    temperature: float
    temp1: float = None
    temp2: float = None
    temp3: float = None
    temp4: float = None
    temp5: float = None
    water_level: WaterLevelData
    pump_status: str = None  # Optional, only for automated systems
    time_stamp: str


# MQTT connection tracking
mqtt_connected = False
mqtt_last_message_time = None

# Prometheus metrics
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint"])
MQTT_MESSAGES = Counter("mqtt_messages_total", "Total MQTT messages processed", ["system_type"])
MQTT_ERRORS = Counter("mqtt_errors_total", "Total MQTT processing errors")
MQTT_CONNECTION = Gauge("mqtt_connected", "MQTT connection status (1=connected, 0=disconnected)")
LAST_DB_WRITE = Gauge("last_db_write_timestamp", "Unix timestamp of last DB write")
CURRENT_TEMPERATURE = Gauge("current_temperature_celsius", "Current average temperature reading")
CURRENT_WATER_LEVEL = Gauge("current_water_level_cm", "Current water depth in cm")
PUMP_STATUS_GAUGE = Gauge("pump_status", "Pump status (1=ON, 0=OFF, -1=N/A)")
SYSTEM_COUNT = Counter("system_data_count", "Total data points by system type", ["system_type"])


def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    connection_messages = {
        0: "Connection successful",
        1: "Connection refused - incorrect protocol version",
        2: "Connection refused - invalid client identifier",
        3: "Connection refused - server unavailable",
        4: "Connection refused - bad username or password",
        5: "Connection refused - not authorized"
    }

    print(f"MQTT Connection: {connection_messages.get(rc, f'Unknown code {rc}')}")

    if rc == 0:
        mqtt_connected = True
        MQTT_CONNECTION.set(1)
        client.subscribe("sensors/data")
        print("✓ Subscribed to topic: sensors/data")
    else:
        mqtt_connected = False
        MQTT_CONNECTION.set(0)


def on_disconnect(client, userdata, rc):
    global mqtt_connected
    print(f"✗ Disconnected from MQTT broker (code: {rc})")
    mqtt_connected = False
    MQTT_CONNECTION.set(0)


def on_message(client, userdata, msg):
    global mqtt_last_message_time
    payload = msg.payload.decode()
    mqtt_last_message_time = datetime.now()

    print(f"\n{'=' * 60}")
    print(f"MQTT Message Received at {mqtt_last_message_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Topic: {msg.topic}")
    print(f"Payload: {payload}")

    session = SessionLocal()
    try:
        data = json.loads(payload)

        # Validate required fields
        required_fields = ["system_type", "temperature", "water_level", "time_stamp"]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Validate system_type
        system_type = data.get("system_type")
        if system_type not in ["conventional", "automated"]:
            raise ValueError(f"Invalid system_type: {system_type}")

        # Extract water level data
        water_level = data.get("water_level")
        if not isinstance(water_level, dict):
            raise ValueError("water_level must be an object")

        # Create database entry
        entry = SolarStillData(
            system_type=system_type,
            temperature=float(data.get("temperature")),
            temp1=float(data.get("temp1")) if data.get("temp1") is not None else None,
            temp2=float(data.get("temp2")) if data.get("temp2") is not None else None,
            temp3=float(data.get("temp3")) if data.get("temp3") is not None else None,
            temp4=float(data.get("temp4")) if data.get("temp4") is not None else None,
            temp5=float(data.get("temp5")) if data.get("temp5") is not None else None,
            water_depth_cm=float(water_level.get("depth_cm")),
            water_raw_adc=int(water_level.get("raw_adc")) if water_level.get("raw_adc") else None,
            pump_status=data.get("pump_status") if system_type == "automated" else None,
            time_stamp=data.get("time_stamp"),
        )

        session.add(entry)
        session.commit()

        # Update Prometheus metrics
        MQTT_MESSAGES.labels(system_type=system_type).inc()
        SYSTEM_COUNT.labels(system_type=system_type).inc()
        LAST_DB_WRITE.set_to_current_time()
        CURRENT_TEMPERATURE.set(entry.temperature)
        CURRENT_WATER_LEVEL.set(entry.water_depth_cm)

        if entry.pump_status == "ON":
            PUMP_STATUS_GAUGE.set(1)
        elif entry.pump_status == "OFF":
            PUMP_STATUS_GAUGE.set(0)
        else:
            PUMP_STATUS_GAUGE.set(-1)

        print(f"✓ Saved to database:")
        print(f"  - ID: {entry.id}")
        print(f"  - System Type: {entry.system_type}")
        print(f"  - Temperature (avg): {entry.temperature}°C")
        if entry.temp1: print(f"  - T1: {entry.temp1}°C")
        if entry.temp2: print(f"  - T2: {entry.temp2}°C")
        if entry.temp3: print(f"  - T3: {entry.temp3}°C")
        if entry.temp4: print(f"  - T4: {entry.temp4}°C")
        if entry.temp5: print(f"  - T5: {entry.temp5}°C")
        print(f"  - Water Depth: {entry.water_depth_cm} cm")
        if entry.pump_status:
            print(f"  - Pump Status: {entry.pump_status}")
        print(f"  - Timestamp: {entry.time_stamp}")
        print(f"{'=' * 60}\n")

    except json.JSONDecodeError as e:
        print(f"✗ JSON decode error: {e}")
        MQTT_ERRORS.inc()
    except ValueError as e:
        print(f"✗ Validation error: {e}")
        MQTT_ERRORS.inc()
    except Exception as e:
        print(f"✗ Error saving to database: {e}")
        MQTT_ERRORS.inc()
        session.rollback()
    finally:
        session.close()


# MQTT client setup
mqtt_client = mqtt.Client(client_id="solar_still_mqtt_client")
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_message = on_message


def mqtt_loop():
    print(f"\n{'=' * 60}")
    print(f"Starting MQTT Client")
    print(f"Broker: {settings.MQTT_BROKER}:{settings.MQTT_PORT}")
    print(f"{'=' * 60}\n")

    try:
        mqtt_client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, 60)
        mqtt_client.loop_forever()
    except Exception as e:
        print(f"✗ MQTT connection error: {e}")
        MQTT_CONNECTION.set(0)


# Start MQTT in background thread
threading.Thread(target=mqtt_loop, daemon=True).start()


# Middleware to track requests
@app.middleware("http")
async def track_requests(request: Request, call_next):
    response = await call_next(request)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    return response


# ========== API Routes ==========

@app.get("/")
def read_root():
    return {
        "message": "Unified Solar Still Monitoring API",
        "version": "2.0.0",
        "supported_systems": ["conventional", "automated"],
        "endpoints": {
            "/data": "Get recent sensor data",
            "/data/latest": "Get most recent reading",
            "/data/range": "Get data within time range",
            "/data/system/{type}": "Get data by system type",
            "/status": "System health check",
            "/stats": "Database statistics",
            "/stats/system/{type}": "Statistics by system type",
            "/publish": "Manually publish data (POST)",
            "/metrics": "Prometheus metrics"
        }
    }


@app.get("/data")
def get_data(
        limit: int = 50,
        system_type: str = None,
        db: Session = Depends(get_db)
):
    """Retrieve recent sensor data (newest first)"""
    query = db.query(SolarStillData)

    if system_type:
        if system_type not in ["conventional", "automated"]:
            raise HTTPException(status_code=400, detail="Invalid system_type")
        query = query.filter(SolarStillData.system_type == system_type)

    rows = query.order_by(SolarStillData.created_at.desc()).limit(limit).all()

    return {
        "count": len(rows),
        "limit": limit,
        "filter": {"system_type": system_type} if system_type else None,
        "data": [format_sensor_data(row) for row in rows],
    }


@app.get("/data/latest")
def get_latest_data(system_type: str = None, db: Session = Depends(get_db)):
    """Get the most recent sensor reading"""
    query = db.query(SolarStillData)

    if system_type:
        if system_type not in ["conventional", "automated"]:
            raise HTTPException(status_code=400, detail="Invalid system_type")
        query = query.filter(SolarStillData.system_type == system_type)

    row = query.order_by(SolarStillData.created_at.desc()).first()

    if not row:
        return {"message": "No data available"}

    return format_sensor_data(row)


@app.get("/data/system/{system_type}")
def get_data_by_system(
        system_type: str,
        limit: int = 50,
        db: Session = Depends(get_db)
):
    """Get data for specific system type"""
    if system_type not in ["conventional", "automated"]:
        raise HTTPException(status_code=400, detail="Invalid system_type")

    rows = db.query(SolarStillData).filter(
        SolarStillData.system_type == system_type
    ).order_by(SolarStillData.created_at.desc()).limit(limit).all()

    return {
        "system_type": system_type,
        "count": len(rows),
        "limit": limit,
        "data": [format_sensor_data(row) for row in rows],
    }


@app.get("/data/range")
def get_data_range(
        start: str,
        end: str,
        system_type: str = None,
        db: Session = Depends(get_db)
):
    """Get data within a time range"""
    try:
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {e}")

    query = db.query(SolarStillData).filter(
        SolarStillData.created_at >= start_dt,
        SolarStillData.created_at <= end_dt
    )

    if system_type:
        if system_type not in ["conventional", "automated"]:
            raise HTTPException(status_code=400, detail="Invalid system_type")
        query = query.filter(SolarStillData.system_type == system_type)

    rows = query.order_by(SolarStillData.created_at.desc()).all()

    return {
        "count": len(rows),
        "start": start,
        "end": end,
        "filter": {"system_type": system_type} if system_type else None,
        "data": [format_sensor_data(row) for row in rows],
    }


@app.post("/publish")
def publish_data(data: SolarStillDataIn, db: Session = Depends(get_db)):
    """Manually publish data directly to database (bypasses MQTT)"""
    if data.system_type not in ["conventional", "automated"]:
        raise HTTPException(status_code=400, detail="Invalid system_type")

    entry = SolarStillData(
        system_type=data.system_type,
        temperature=data.temperature,
        temp1=data.temp1,
        temp2=data.temp2,
        temp3=data.temp3,
        temp4=data.temp4,
        temp5=data.temp5,
        water_depth_cm=data.water_level.depth_cm,
        water_raw_adc=data.water_level.raw_adc,
        pump_status=data.pump_status if data.system_type == "automated" else None,
        time_stamp=data.time_stamp,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    LAST_DB_WRITE.set_to_current_time()
    CURRENT_TEMPERATURE.set(entry.temperature)
    CURRENT_WATER_LEVEL.set(entry.water_depth_cm)
    SYSTEM_COUNT.labels(system_type=entry.system_type).inc()

    return {
        "status": "saved",
        "entry": format_sensor_data(entry)
    }


@app.get("/stats")
def get_statistics(db: Session = Depends(get_db)):
    """Get overall database statistics"""
    total_count = db.query(func.count(SolarStillData.id)).scalar()

    if total_count == 0:
        return {"message": "No data available"}

    conv_count = db.query(func.count(SolarStillData.id)).filter(
        SolarStillData.system_type == "conventional"
    ).scalar()

    auto_count = db.query(func.count(SolarStillData.id)).filter(
        SolarStillData.system_type == "automated"
    ).scalar()

    avg_temp = db.query(func.avg(SolarStillData.temperature)).scalar()
    min_temp = db.query(func.min(SolarStillData.temperature)).scalar()
    max_temp = db.query(func.max(SolarStillData.temperature)).scalar()

    avg_water = db.query(func.avg(SolarStillData.water_depth_cm)).scalar()
    min_water = db.query(func.min(SolarStillData.water_depth_cm)).scalar()
    max_water = db.query(func.max(SolarStillData.water_depth_cm)).scalar()

    first_entry = db.query(SolarStillData).order_by(SolarStillData.created_at.asc()).first()
    last_entry = db.query(SolarStillData).order_by(SolarStillData.created_at.desc()).first()

    return {
        "total_records": total_count,
        "system_breakdown": {
            "conventional": conv_count,
            "automated": auto_count
        },
        "temperature": {
            "average": round(avg_temp, 2),
            "min": round(min_temp, 2),
            "max": round(max_temp, 2),
            "unit": "°C"
        },
        "water_level": {
            "average": round(avg_water, 2),
            "min": round(min_water, 2),
            "max": round(max_water, 2),
            "unit": "cm"
        },
        "time_range": {
            "first_record": first_entry.created_at.isoformat() if first_entry else None,
            "last_record": last_entry.created_at.isoformat() if last_entry else None,
        }
    }


@app.get("/stats/system/{system_type}")
def get_system_statistics(system_type: str, db: Session = Depends(get_db)):
    """Get statistics for specific system type"""
    if system_type not in ["conventional", "automated"]:
        raise HTTPException(status_code=400, detail="Invalid system_type")

    count = db.query(func.count(SolarStillData.id)).filter(
        SolarStillData.system_type == system_type
    ).scalar()

    if count == 0:
        return {"message": f"No data available for {system_type} systems"}

    avg_temp = db.query(func.avg(SolarStillData.temperature)).filter(
        SolarStillData.system_type == system_type
    ).scalar()

    min_temp = db.query(func.min(SolarStillData.temperature)).filter(
        SolarStillData.system_type == system_type
    ).scalar()

    max_temp = db.query(func.max(SolarStillData.temperature)).filter(
        SolarStillData.system_type == system_type
    ).scalar()

    avg_water = db.query(func.avg(SolarStillData.water_depth_cm)).filter(
        SolarStillData.system_type == system_type
    ).scalar()

    result = {
        "system_type": system_type,
        "total_records": count,
        "temperature": {
            "average": round(avg_temp, 2),
            "min": round(min_temp, 2),
            "max": round(max_temp, 2),
            "unit": "°C"
        },
        "water_level": {
            "average": round(avg_water, 2),
            "unit": "cm"
        }
    }

    if system_type == "automated":
        pump_on = db.query(func.count(SolarStillData.id)).filter(
            SolarStillData.system_type == "automated",
            SolarStillData.pump_status == "ON"
        ).scalar()

        pump_off = db.query(func.count(SolarStillData.id)).filter(
            SolarStillData.system_type == "automated",
            SolarStillData.pump_status == "OFF"
        ).scalar()

        result["pump_statistics"] = {
            "on_count": pump_on,
            "off_count": pump_off,
            "on_percentage": round((pump_on / count) * 100, 2) if count > 0 else 0
        }

    return result


@app.get("/status")
def get_status(db: Session = Depends(get_db)):
    """Check system health (FastAPI, MQTT, Database)"""
    last_entry = db.query(SolarStillData).order_by(SolarStillData.created_at.desc()).first()

    time_since_last_msg = None
    if mqtt_last_message_time:
        delta = datetime.now() - mqtt_last_message_time
        time_since_last_msg = f"{delta.seconds}s ago"

    return {
        "fastapi_status": "online",
        "mqtt_status": "connected" if mqtt_connected else "disconnected",
        "mqtt_broker": f"{settings.MQTT_BROKER}:{settings.MQTT_PORT}",
        "mqtt_last_message": time_since_last_msg,
        "database_status": "ok" if last_entry else "no data yet",
        "database_url": f"{settings.POSTGRESQL_HOST}:{settings.POSTGRESQL_PORT}/{settings.POSTGRESQL_DBNAME}",
        "last_data": format_sensor_data(last_entry) if last_entry else None,
    }


@app.get("/metrics")
def metrics():
    """Prometheus scrape endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.delete("/data/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    """Delete a specific record by ID"""
    record = db.query(SolarStillData).filter(SolarStillData.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    db.delete(record)
    db.commit()
    return {"status": "deleted", "id": record_id}


# Helper function to format sensor data
def format_sensor_data(row):
    data = {
        "id": row.id,
        "system_type": row.system_type,
        "temperature": row.temperature,
        "temperatures": {
            "T1": row.temp1,
            "T2": row.temp2,
            "T3": row.temp3,
            "T4": row.temp4,
            "T5": row.temp5,
        },
        "water_level": {
            "depth_cm": row.water_depth_cm,
            "raw_adc": row.water_raw_adc,
        },
        "time_stamp": row.time_stamp,
        "created_at": row.created_at.isoformat(),
    }

    if row.system_type == "automated":
        data["pump_status"] = row.pump_status

    return data


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)