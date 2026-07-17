"""
schemas/device.py
Schema Pydantic untuk device (sensor/aktuator) dan perintah kontrol.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DeviceResponse(BaseModel):
    id: int
    device_code: str
    name: str
    type: str
    is_online: bool
    is_on: bool
    last_seen: datetime

    class Config:
        from_attributes = True


class DeviceCommand(BaseModel):
    command: str  # "ON" atau "OFF"
