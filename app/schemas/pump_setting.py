"""
schemas/pump_setting.py
Schema Pydantic untuk pengaturan mode otomatis & ambang batas pompa.
"""

from pydantic import BaseModel


class PumpSettingResponse(BaseModel):
    auto_mode: bool
    threshold_percent: float

    class Config:
        from_attributes = True


class PumpSettingUpdate(BaseModel):
    auto_mode: bool | None = None
    threshold_percent: float | None = None
