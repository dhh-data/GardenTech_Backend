"""
api/devices.py
Endpoint device & aktuator. Prefix "/devices" cocok dengan
APP_CONFIG.DEVICES_ENDPOINT & ACTUATOR_COMMAND_ENDPOINT di frontend.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.models.device import Device
from app.models.pump_setting import PumpSetting
from app.models.log import ActivityLog
from app.schemas.device import DeviceResponse, DeviceCommand
from app.mqtt_client import publish_command

router = APIRouter(
    prefix="/devices",
    tags=["Devices"]
)


# DAFTAR DEVICE UNTUK HALAMAN DEVICES
@router.get("/", response_model=List[DeviceResponse])
def get_devices(db: Session = Depends(get_db)):
    return db.query(Device).order_by(Device.id.asc()).all()


@router.get("/{device_code}", response_model=DeviceResponse)
def get_device(device_code: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.device_code == device_code).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device tidak ditemukan")
    return device


# KONTROL AKTUATOR (ON/OFF) - dipanggil dari halaman Actuators & tombol "Siram manual"
@router.post("/{device_code}/command")
def send_command(device_code: str, payload: DeviceCommand, db: Session = Depends(get_db)):

    device = db.query(Device).filter(Device.device_code == device_code).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device tidak ditemukan")

    if payload.command not in ("ON", "OFF"):
        raise HTTPException(status_code=400, detail="command harus 'ON' atau 'OFF'")

    device.is_on = payload.command == "ON"
    db.add(device)

    # kalau device ini pompa/relay (bukan buzzer/LED), matikan mode otomatis (perintah manual menang)
    if device_code in ("dev002", "dev003"):
        setting = db.query(PumpSetting).first()
        if setting:
            setting.auto_mode = False
            db.add(setting)

    db.add(ActivityLog(
        type="success" if device.is_on else "info",
        message=f"{device.name} di-{payload.command.lower()} secara manual",
    ))

    db.commit()
    db.refresh(device)

    # publish ke ESP32 via MQTT (kalau broker terhubung)
    published = publish_command(device_code, payload.command)

    return {
        "message": f"Perintah {payload.command} {'terkirim ke ESP32 via MQTT' if published else 'tersimpan (MQTT belum terhubung)'}",
        "device": device,
        "mqtt_published": published,
    }