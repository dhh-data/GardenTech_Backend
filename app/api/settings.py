"""
api/settings.py
Endpoint pengaturan pompa: mode otomatis ON/OFF dan ambang batas
kelembapan. Dipakai toggle "Mode otomatis" di Dashboard.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.pump_setting import PumpSetting
from app.schemas.pump_setting import PumpSettingResponse, PumpSettingUpdate

router = APIRouter(
    prefix="/settings",
    tags=["Settings"]
)


def _get_or_create(db: Session) -> PumpSetting:
    setting = db.query(PumpSetting).first()
    if not setting:
        setting = PumpSetting(auto_mode=True, threshold_percent=40.0)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


@router.get("/pump", response_model=PumpSettingResponse)
def get_pump_setting(db: Session = Depends(get_db)):
    return _get_or_create(db)


@router.put("/pump", response_model=PumpSettingResponse)
def update_pump_setting(payload: PumpSettingUpdate, db: Session = Depends(get_db)):
    setting = _get_or_create(db)

    if payload.auto_mode is not None:
        setting.auto_mode = payload.auto_mode
    if payload.threshold_percent is not None:
        setting.threshold_percent = payload.threshold_percent

    db.commit()
    db.refresh(setting)
    return setting
