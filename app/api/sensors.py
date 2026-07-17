"""
api/sensors.py
Endpoint sensor: ESP32 kirim data ke sini (POST), frontend ambil data
terbaru & histori dari sini (GET). Prefix "/sensors" cocok dengan
APP_CONFIG.SENSORS_LATEST_ENDPOINT & SENSORS_HISTORY_ENDPOINT di frontend.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.database import get_db
from app.models.sensor_reading import SensorReading
from app.models.pump_setting import PumpSetting
from app.models.log import ActivityLog
from app.models.device import Device

from app.schemas.sensor import (
    SensorReadingCreate,
    SensorLatestResponse,
    SensorHistoryResponse,
    VoltageCurrentHistoryResponse,
)

router = APIRouter(
    prefix="/sensors",
    tags=["Sensors"]
)


def _get_or_create_pump_setting(db: Session) -> PumpSetting:
    """pump_settings cuma boleh ada 1 baris, dibuat otomatis kalau belum ada."""
    setting = db.query(PumpSetting).first()
    if not setting:
        setting = PumpSetting(auto_mode=True, threshold_percent=40.0)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


# ESP32 KIRIM DATA SENSOR KE SINI
@router.post("/", status_code=201)
def save_sensor_data(payload: SensorReadingCreate, db: Session = Depends(get_db)):

    setting = _get_or_create_pump_setting(db)

    # tentukan status pompa: kalau mode otomatis aktif, nyala kalau di bawah ambang batas
    pump_on = False
    if setting.auto_mode and payload.soil_moisture is not None:
        pump_on = payload.soil_moisture < setting.threshold_percent

    pump_voltage = payload.pump_voltage or 0
    pump_current = payload.pump_current or 0
    pump_power = round(pump_voltage * pump_current, 2)

    reading = SensorReading(
        soil_moisture=payload.soil_moisture,
        air_temp=payload.air_temp,
        pump_voltage=pump_voltage,
        pump_current=pump_current,
        pump_power=pump_power,
        ultrasonic_detected=payload.ultrasonic_detected or False,
        pump_on=pump_on,
        air_humidity=payload.air_humidity,
        distance_cm=payload.distance_cm,
    )
    db.add(reading)

    # catat log otomatis kalau ada kejadian penting
    if payload.ultrasonic_detected:
        db.add(ActivityLog(
            type="warning",
            message="Objek terdeteksi di area kebun (sensor ultrasonic)"
        ))

    db.commit()
    db.refresh(reading)

    return {"message": "Data sensor tersimpan", "reading_id": reading.id}


# DASHBOARD AMBIL DATA TERBARU DARI SINI (polling tiap beberapa detik)
@router.get("/latest", response_model=SensorLatestResponse)
def get_latest_sensor(db: Session = Depends(get_db)):

    latest = (
        db.query(SensorReading)
        .order_by(desc(SensorReading.recorded_at))
        .first()
    )
    setting = _get_or_create_pump_setting(db)

    if not latest:
        # belum ada data sama sekali (ESP32 belum pernah kirim) -> kembalikan nilai netral
        return SensorLatestResponse(
            soilMoisture=0,
            airTemp=0,
            pumpVoltage=0,
            pumpCurrent=0,
            pumpPower=0,
            ultrasonicDetected=False,
            pumpOn=False,
            autoMode=setting.auto_mode,
            threshold=setting.threshold_percent,
            airHumidity=0,
            distanceCm=0,
        )

    return SensorLatestResponse(
        soilMoisture=latest.soil_moisture or 0,
        airTemp=latest.air_temp or 0,
        pumpVoltage=latest.pump_voltage or 0,
        pumpCurrent=latest.pump_current or 0,
        pumpPower=latest.pump_power or 0,
        ultrasonicDetected=latest.ultrasonic_detected,
        pumpOn=latest.pump_on,
        autoMode=setting.auto_mode,
        threshold=setting.threshold_percent,
        airHumidity=latest.air_humidity or 0,
        distanceCm=latest.distance_cm or 0,
    )


# GRAFIK "TREN KELEMBAPAN TANAH (24 JAM)" DI DASHBOARD
@router.get("/history/moisture", response_model=SensorHistoryResponse)
def get_moisture_history(db: Session = Depends(get_db)):

    since = datetime.utcnow() - timedelta(hours=24)
    rows = (
        db.query(SensorReading)
        .filter(SensorReading.recorded_at >= since)
        .filter(SensorReading.soil_moisture.isnot(None))
        .order_by(SensorReading.recorded_at.asc())
        .all()
    )

    labels = [r.recorded_at.strftime("%H:%M") for r in rows]
    values = [r.soil_moisture for r in rows]

    return SensorHistoryResponse(labels=labels, values=values)


# GRAFIK VOLTAGE/CURRENT DI HALAMAN CHARTS & HISTORY
@router.get("/history/voltage-current", response_model=VoltageCurrentHistoryResponse)
def get_voltage_current_history(days: int = 7, db: Session = Depends(get_db)):

    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(SensorReading)
        .filter(SensorReading.recorded_at >= since)
        .order_by(SensorReading.recorded_at.asc())
        .all()
    )

    labels = [r.recorded_at.strftime("%d/%m") for r in rows]
    voltage = [r.pump_voltage or 0 for r in rows]
    current = [r.pump_current or 0 for r in rows]

    return VoltageCurrentHistoryResponse(labels=labels, voltage=voltage, current=current)


# LIST SENSOR + NILAI TERBARU UNTUK HALAMAN SENSORS
@router.get("/list")
def get_sensor_list(db: Session = Depends(get_db)):

    latest = (
        db.query(SensorReading)
        .order_by(desc(SensorReading.recorded_at))
        .first()
    )
    setting = _get_or_create_pump_setting(db)

    if not latest:
        return []

    return [
        {
            "id": "sn001",
            "name": "Soil Moisture Sensor",
            "value": f"{latest.soil_moisture or 0}%",
            "status": "warning" if (latest.soil_moisture or 0) < setting.threshold_percent else "normal",
        },
        {
            "id": "sn002",
            "name": "DHT22 - Suhu udara",
            "value": f"{latest.air_temp or 0}°C",
            "status": "normal",
        },
        {
            "id": "sn003",
            "name": "INA219 - Tegangan pompa",
            "value": f"{latest.pump_voltage or 0} V",
            "status": "normal",
        },
        {
            "id": "sn004",
            "name": "INA219 - Arus pompa",
            "value": f"{latest.pump_current or 0} A",
            "status": "normal",
        },
        {
            "id": "sn005",
            "name": "Sensor Ultrasonic - Jarak objek",
            "value": "Objek terdeteksi" if latest.ultrasonic_detected else "Tidak ada objek",
            "status": "warning" if latest.ultrasonic_detected else "normal",
        },
    ]