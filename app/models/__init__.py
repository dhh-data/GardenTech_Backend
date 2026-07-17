"""
models/__init__.py
Import semua model di sini supaya saat Base.metadata.create_all()
dipanggil dari main.py, SQLAlchemy tahu semua tabel yang harus dibuat.
"""

from app.models.user import User
from app.models.device import Device
from app.models.sensor_reading import SensorReading
from app.models.log import ActivityLog
from app.models.pump_setting import PumpSetting
