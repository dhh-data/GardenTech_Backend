"""
models/device.py
Tabel 'devices' - daftar perangkat keras yang terhubung ke sistem
(ESP32, sensor, relay, dll), ditampilkan di halaman Devices & Actuators.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import TIMESTAMP
from sqlalchemy.sql import func

from app.database.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)

    # id unik yang dipakai juga sebagai identitas di topic MQTT, contoh: "dev001"
    device_code = Column(String(50), unique=True, nullable=False, index=True)

    name = Column(String(100), nullable=False)

    # "sensor" atau "actuator"
    type = Column(String(20), nullable=False)

    is_online = Column(Boolean, default=False)

    # untuk aktuator (relay/pompa): status ON/OFF saat ini
    is_on = Column(Boolean, default=False)

    last_seen = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now()
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )
