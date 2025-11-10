import os
import json
import threading
from datetime import datetime
from fastapi import FastAPI, Depends, Request, Response
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine, Column, Integer, Float, String, BigInteger, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import paho.mqtt.client as mqtt

# Prometheus client
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST


class Settings(BaseSettings):
    # Database settings
    POSTGRESQL_URI: str = ""
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
app = FastAPI(title="IoT Sensor Data API", version="1.0.0")

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


# Enhanced Database model with temp1 and temp2
class SensorData(Base):
    __tablename__ = "pyranometer"

    id = Column(BigInteger, primary_key=True, index=True)
    temperature = Column(Float, nullable=False)  # Average temperature
    light_intensity = Column(Float, nullable=False)
    time_stamp = Column(String, nullable=True)  # ISO8601 from ESP32 RTC
    temp1 = Column(Float, nullable=True)  # Thermistor 1 (GPIO 33)
    temp2 = Column(Float, nullable=True)  # Thermistor 2 (GPIO 32)
    created_at = Column(DateTime, server_default=func.now())


Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Input models
class DataIn(BaseModel):
    temperature: float
    light_intensity: float
    time_stamp: str
    temp1: float = None  # Optional
    temp2: float = None  # Optional


# MQTT connection tracking
mqtt_connected = False
mqtt_last_message_time = None

# Prometheus metrics
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint"])
MQTT_MESSAGES = Counter("mqtt_messages_total", "Total MQTT messages processed")
MQTT_ERRORS = Counter("mqtt_errors_total", "Total MQTT processing errors")
MQTT_CONNECTION = Gauge("mqtt_connected", "MQTT connection status (1=connected, 0=disconnected)")
LAST_DB_WRITE = Gauge("last_db_write_timestamp", "Unix timestamp of last DB write")
CURRENT_TEMPERATURE = Gauge("current_temperature_celsius", "Current temperature reading")
CURRENT_LIGHT = Gauge("current_light_intensity_lux", "Current light intensity reading")


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
        required_fields = ["temperature", "light_intensity", "time_stamp"]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Create database entry
        entry = SensorData(
            temperature=float(data.get("temperature")),
            light_intensity=float(data.get("light_intensity")),
            time_stamp=data.get("time_stamp"),
            temp1=float(data.get("temp1")) if data.get("temp1") is not None else None,
            temp2=float(data.get("temp2")) if data.get("temp2") is not None else None,
        )

        session.add(entry)
        session.commit()

        # Update Prometheus metrics
        MQTT_MESSAGES.inc()
        LAST_DB_WRITE.set_to_current_time()
        CURRENT_TEMPERATURE.set(entry.temperature)
        CURRENT_LIGHT.set(entry.light_intensity)

        print(f"✓ Saved to database:")
        print(f"  - ID: {entry.id}")
        print(f"  - Temperature: {entry.temperature}°C (avg)")
        print(f"  - Temp1: {entry.temp1}°C" if entry.temp1 else "  - Temp1: N/A")
        print(f"  - Temp2: {entry.temp2}°C" if entry.temp2 else "  - Temp2: N/A")
        print(f"  - Light: {entry.light_intensity} lux")
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
mqtt_client = mqtt.Client(client_id="fastapi_mqtt_client")
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
        "message": "IoT Sensor Data API",
        "version": "1.0.0",
        "endpoints": {
            "/data": "Get recent sensor data",
            "/status": "System health check",
            "/stats": "Database statistics",
            "/publish": "Manually publish data (POST)",
            "/metrics": "Prometheus metrics"
        }
    }


@app.get("/data")
def get_data(limit: int = 50, db: Session = Depends(get_db)):
    """Retrieve recent sensor data (newest first)"""
    rows = db.query(SensorData).order_by(SensorData.created_at.desc()).limit(limit).all()
    return {
        "count": len(rows),
        "limit": limit,
        "data": [
            {
                "id": row.id,
                "temperature": row.temperature,
                "temp1": row.temp1,
                "temp2": row.temp2,
                "light_intensity": row.light_intensity,
                "time_stamp": row.time_stamp,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ],
    }


@app.get("/data/latest")
def get_latest_data(db: Session = Depends(get_db)):
    """Get the most recent sensor reading"""
    row = db.query(SensorData).order_by(SensorData.created_at.desc()).first()
    if not row:
        return {"message": "No data available"}

    return {
        "id": row.id,
        "temperature": row.temperature,
        "temp1": row.temp1,
        "temp2": row.temp2,
        "light_intensity": row.light_intensity,
        "time_stamp": row.time_stamp,
        "created_at": row.created_at.isoformat(),
    }


@app.get("/data/range")
def get_data_range(start: str, end: str, db: Session = Depends(get_db)):
    """Get data within a time range

    Args:
        start: ISO format datetime (e.g., 2025-11-10T00:00:00Z)
        end: ISO format datetime
    """
    try:
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
    except ValueError as e:
        return {"error": f"Invalid datetime format: {e}"}

    rows = db.query(SensorData).filter(
        SensorData.created_at >= start_dt,
        SensorData.created_at <= end_dt
    ).order_by(SensorData.created_at.desc()).all()

    return {
        "count": len(rows),
        "start": start,
        "end": end,
        "data": [
            {
                "id": row.id,
                "temperature": row.temperature,
                "temp1": row.temp1,
                "temp2": row.temp2,
                "light_intensity": row.light_intensity,
                "time_stamp": row.time_stamp,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ],
    }


@app.post("/publish")
def publish_data(data: DataIn, db: Session = Depends(get_db)):
    """Manually publish data directly to database (bypasses MQTT)"""
    entry = SensorData(
        temperature=data.temperature,
        light_intensity=data.light_intensity,
        time_stamp=data.time_stamp,
        temp1=data.temp1,
        temp2=data.temp2,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    LAST_DB_WRITE.set_to_current_time()
    CURRENT_TEMPERATURE.set(entry.temperature)
    CURRENT_LIGHT.set(entry.light_intensity)

    return {
        "status": "saved",
        "entry": {
            "id": entry.id,
            "temperature": entry.temperature,
            "temp1": entry.temp1,
            "temp2": entry.temp2,
            "light_intensity": entry.light_intensity,
            "time_stamp": entry.time_stamp,
            "created_at": entry.created_at.isoformat(),
        }
    }


@app.get("/stats")
def get_statistics(db: Session = Depends(get_db)):
    """Get database statistics and aggregations"""
    total_count = db.query(func.count(SensorData.id)).scalar()

    if total_count == 0:
        return {"message": "No data available"}

    avg_temp = db.query(func.avg(SensorData.temperature)).scalar()
    min_temp = db.query(func.min(SensorData.temperature)).scalar()
    max_temp = db.query(func.max(SensorData.temperature)).scalar()

    avg_light = db.query(func.avg(SensorData.light_intensity)).scalar()
    min_light = db.query(func.min(SensorData.light_intensity)).scalar()
    max_light = db.query(func.max(SensorData.light_intensity)).scalar()

    first_entry = db.query(SensorData).order_by(SensorData.created_at.asc()).first()
    last_entry = db.query(SensorData).order_by(SensorData.created_at.desc()).first()

    return {
        "total_records": total_count,
        "temperature": {
            "average": round(avg_temp, 2),
            "min": round(min_temp, 2),
            "max": round(max_temp, 2),
            "unit": "°C"
        },
        "light_intensity": {
            "average": round(avg_light, 2),
            "min": round(min_light, 2),
            "max": round(max_light, 2),
            "unit": "lux"
        },
        "time_range": {
            "first_record": first_entry.created_at.isoformat() if first_entry else None,
            "last_record": last_entry.created_at.isoformat() if last_entry else None,
        }
    }


@app.get("/status")
def get_status(db: Session = Depends(get_db)):
    """Check system health (FastAPI, MQTT, Database)"""
    last_entry = db.query(SensorData).order_by(SensorData.created_at.desc()).first()

    # Calculate time since last message
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
        "last_data": {
            "id": last_entry.id,
            "temperature": last_entry.temperature,
            "temp1": last_entry.temp1,
            "temp2": last_entry.temp2,
            "light_intensity": last_entry.light_intensity,
            "time_stamp": last_entry.time_stamp,
            "created_at": last_entry.created_at.isoformat(),
        } if last_entry else None,
    }


@app.get("/metrics")
def metrics():
    """Prometheus scrape endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.delete("/data/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    """Delete a specific record by ID"""
    record = db.query(SensorData).filter(SensorData.id == record_id).first()
    if not record:
        return {"error": "Record not found"}

    db.delete(record)
    db.commit()
    return {"status": "deleted", "id": record_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)