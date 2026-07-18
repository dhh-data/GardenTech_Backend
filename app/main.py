"""
main.py
Entry point aplikasi. Jalankan dengan:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
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
    redirect_slashes=False,
)

# ---------- MQTT startup ----------
@app.on_event("startup")
def startup_event():
    from app.mqtt_client import start_mqtt
    start_mqtt()

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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