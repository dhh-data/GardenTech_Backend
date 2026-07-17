"""
models/pump_setting.py
Tabel 'pump_settings' - cuma 1 baris (single-row config), menyimpan
mode otomatis ON/OFF dan ambang batas kelembapan untuk trigger pompa.
Dipakai di Dashboard (toggle "Mode otomatis" & "Ambang batas siram").
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Boolean
from sqlalchemy import Float

from app.database.database import Base


class PumpSetting(Base):
    __tablename__ = "pump_settings"

    id = Column(Integer, primary_key=True, index=True)

    auto_mode = Column(Boolean, default=True)

    threshold_percent = Column(Float, default=40.0)  # pompa nyala kalau soil_moisture < nilai ini
