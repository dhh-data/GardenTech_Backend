"""
schemas/log.py
Schema Pydantic untuk activity log (riwayat aktivitas sistem).
"""

from datetime import datetime
from pydantic import BaseModel


class LogResponse(BaseModel):
    time: str    # jam saja, format "HH:MM", sesuai tampilan di frontend
    type: str    # "info" / "success" / "warning" / "danger"
    text: str

    class Config:
        from_attributes = True


class LogCreate(BaseModel):
    type: str = "info"
    message: str
