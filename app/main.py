"""
main.py
Entry point aplikasi. Jalankan dengan:
    uvicorn app.main:app --reload

Bedanya dengan contoh dosen:
- ada CORS middleware (wajib, karena frontend dibuka dari file://
  atau live server yang originnya beda dengan backend)
- otomatis bikin semua tabel di MySQL saat startup (Base.metadata.create_all)
- router di-prefix "/api/v1" supaya cocok persis dengan
  APP_CONFIG.API_BASE_URL = "http://localhost:8000/api/v1" di frontend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.database.database import engine, Base
from app.models import user, device, sensor_reading, log, pump_setting  # noqa: F401

from app.api import auth
from app.api import users
from app.api import sensors
from app.api import devices
from app.api import logs
from app.api import settings
from app.api import mqtt as mqtt_router

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Garden Backend API",
    version="1.0",
    description="Backend untuk dashboard monitoring & kontrol Smart Garden Kit (ESP32 + MQTT HiveMQ).",
)

# ---------- MQTT startup ----------
@app.on_event("startup")
def startup_event():
    from app.mqtt_client import start_mqtt
    start_mqtt()

# ---------- CORS ----------
cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in cors_origins_raw.split(",")] if cors_origins_raw != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Smart Garden Backend API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


API_PREFIX = "/api/v1"

app.include_router(auth.router,        prefix=API_PREFIX)
app.include_router(users.router,       prefix=API_PREFIX)
app.include_router(sensors.router,     prefix=API_PREFIX)
app.include_router(devices.router,     prefix=API_PREFIX)
app.include_router(logs.router,        prefix=API_PREFIX)
app.include_router(settings.router,    prefix=API_PREFIX)
app.include_router(mqtt_router.router, prefix=API_PREFIX)
