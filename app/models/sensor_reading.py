"""
models/sensor_reading.py
Tabel 'sensor_readings' - histori pembacaan sensor (soil moisture, suhu,
tegangan/arus pompa dari INA219, dan status ultrasonic).
Setiap kali ESP32 kirim data, satu baris baru ditambahkan di sini.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Float
from sqlalchemy import Boolean
from sqlalchemy import TIMESTAMP
from sqlalchemy.sql import func

from app.database.database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)

    soil_moisture = Column(Float, nullable=True)     # %, dari capacitive soil moisture sensor
    air_temp = Column(Float, nullable=True)            # °C, dari DHT22
    pump_voltage = Column(Float, nullable=True)         # V, dari INA219
    pump_current = Column(Float, nullable=True)          # A, dari INA219
    pump_power = Column(Float, nullable=True)             # W, dihitung (V x A)

    ultrasonic_detected = Column(Boolean, default=False)   # true kalau ada objek terdeteksi
    pump_on = Column(Boolean, default=False)                 # status relay pompa saat itu

    air_humidity = Column(Float, nullable=True)             # %, kelembaban udara dari DHT22
    distance_cm = Column(Float, nullable=True)               # cm, jarak objek dari sensor ultrasonic

    recorded_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        index=True
    )