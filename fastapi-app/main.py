import os
import json
import threading
from fastapi import FastAPI, Depends, Request
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine, Column, Integer, Float, String,BigInteger,DateTime,func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import paho.mqtt.client as mqtt

# Prometheus client
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST


class Settings(BaseSettings):
    # Database settings
    POSTGRESQL_URI:str
    POSTGRESQL_HOST: str
    POSTGRESQL_PORT: str
    POSTGRESQL_USER: str
    POSTGRESQL_PASSWORD: str
    POSTGRESQL_DBNAME: str

    class Config:
        env_file = ".env"


settings = Settings()

# FastAPI Setup
app = FastAPI()

# Database Setup
DATABASE_URL = f"postgresql+psycopg2://{settings.POSTGRESQL_USER}:{settings.POSTGRESQL_PASSWORD}@{settings.POSTGRESQL_HOST}:{settings.POSTGRESQL_PORT}/{settings.POSTGRESQL_DBNAME}"



engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        print("Connection successful!")
except Exception as e:
    print(f"Failed to connect: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database model
class SensorData(Base):
    __tablename__ = "pyranometer"

    id = Column(BigInteger, primary_key=True, index=True)
    temperature = Column(Float, nullable=False)
    light_intensity = Column(Float, nullable=False)
    time_stamp = Column(String, nullable=True)  # match Supabase column nam
    created_at = Column(DateTime, server_default=func.now())


Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Input model
class DataIn(BaseModel):
    temperature: float
    light_intensity: float
    time_stamp: str  # ISO8601 string from ESP32 RTC


# MQTT callbacks
mqtt_connected = False  # track connection status

# Prometheus metrics
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint"])
MQTT_MESSAGES = Counter("mqtt_messages_total", "Total MQTT messages processed")
MQTT_CONNECTION = Gauge("mqtt_connected", "MQTT connection status (1=connected, 0=disconnected)")
LAST_DB_WRITE = Gauge("last_db_write_timestamp", "Unix timestamp of last DB write")


def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    print("Connected to MQTT with result code " + str(rc))
    if rc == 0:
        mqtt_connected = True
        MQTT_CONNECTION.set(1)
    client.subscribe("sensors/data")


def on_disconnect(client, userdata, rc):
    global mqtt_connected
    print("Disconnected from MQTT broker")
    mqtt_connected = False
    MQTT_CONNECTION.set(0)


def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"Received message: {payload}")
    session = SessionLocal()
    try:
        data = json.loads(payload)
        entry = SensorData(
            temperature=float(data.get("temperature")),
            light_intensity=float(data.get("light_intensity")),
            time_stamp=data.get("time_stamp"),
        )
        session.add(entry)
        session.commit()
        MQTT_MESSAGES.inc()
        LAST_DB_WRITE.set_to_current_time()
    except Exception as e:
        print("Error saving to DB:", e)
        session.rollback()
    finally:
        session.close()


mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_message = on_message


def mqtt_loop():
    mqtt_client.connect(os.getenv("MQTT_BROKER", "localhost"), int(os.getenv("MQTT_PORT", 1883)), 60)
    mqtt_client.loop_forever()


threading.Thread(target=mqtt_loop, daemon=True).start()


# Middleware to track request
@app.middleware("http")
async def track_requests(request: Request, call_next):
    response = await call_next(request)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    return response


# FastAPI Routes
@app.get("/")
def read_root():
    return {"message": "FastAPI + MQTT + PostgreSQL running"}


@app.get("/data")
def get_data(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(SensorData).order_by(SensorData.id.desc()).limit(limit).all()
    return {
        "count": len(rows),
        "data": [
            {
                "id": row.id,
                "temperature": row.temperature,
                "light_intensity": row.light_intensity,
                "time_stamp": row.time_stamp,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ],
    }


@app.post("/publish/")
def publish_data(data: DataIn, db: Session = Depends(get_db)):
    """Publish directly into DB (bypasses MQTT)."""
    entry = SensorData(
        temperature=data.temperature,
        light_intensity=data.light_intensity,
        time_stamp=data.time_stamp,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    LAST_DB_WRITE.set_to_current_time()
    return {"status": "saved", "entry": {
        "id": entry.id,
        "temperature": entry.temperature,
        "light_intensity": entry.light_intensity,
        "time_stamp": entry.time_stamp,
        "created_at": entry.created_at.isoformat(),
    }}


@app.get("/status/")
def get_status(db: Session = Depends(get_db)):
    """Check system health (FastAPI, MQTT, Database)."""
    last_entry = db.query(SensorData).order_by(SensorData.created_at.desc()).first()
    return {
        "fastapi_status": "online",
        "mqtt_status": "connected" if mqtt_connected else "disconnected",
        "database_status": "ok" if last_entry else "no data yet",
        "last_data": {
            "id": last_entry.id if last_entry else None,
            "time_stamp": last_entry.time_stamp if last_entry else None,
            "created_at": last_entry.created_at.isoformat() if last_entry else None,
        } if last_entry else None,
    }


@app.get("/metrics")
def metrics():
    """Prometheus scrape endpoint"""
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}
