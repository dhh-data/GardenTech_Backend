"""
schemas/sensor.py
Schema Pydantic untuk data sensor (sesuai field yang dibaca dashboard.js
di frontend: soilMoisture, airTemp, pumpPower, dll).
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class SensorReadingCreate(BaseModel):
    """Dipakai saat ESP32 mengirim data sensor baru ke backend."""
    soil_moisture: Optional[float] = None
    air_temp: Optional[float] = None
    pump_voltage: Optional[float] = None
    pump_current: Optional[float] = None
    ultrasonic_detected: Optional[bool] = False
    air_humidity: Optional[float] = None
    distance_cm: Optional[float] = None


class SensorLatestResponse(BaseModel):
    """Response untuk GET /sensors/latest - field-nya sengaja camelCase
    biar pas dipakai langsung di dashboard.js tanpa perlu mapping ulang."""
    soilMoisture: float
    airTemp: float
    pumpVoltage: float
    pumpCurrent: float
    pumpPower: float
    ultrasonicDetected: bool
    pumpOn: bool
    autoMode: bool
    threshold: float
    airHumidity: float = 0
    distanceCm: float = 0


class SensorHistoryPoint(BaseModel):
    label: str
    value: float


class SensorHistoryResponse(BaseModel):
    labels: List[str]
    values: List[float]


class VoltageCurrentHistoryResponse(BaseModel):
    labels: List[str]
    voltage: List[float]
    current: List[float]