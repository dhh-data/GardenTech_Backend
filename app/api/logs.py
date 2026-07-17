"""
api/logs.py
Endpoint log aktivitas. Prefix "/logs" cocok dengan
APP_CONFIG.LOGS_ENDPOINT di frontend.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from app.database.database import get_db
from app.models.log import ActivityLog
from app.schemas.log import LogResponse, LogCreate

router = APIRouter(
    prefix="/logs",
    tags=["Logs"]
)


# DAFTAR LOG, TERBARU DULU - dipakai halaman Logs (limit besar) & cuplikan Dashboard (limit kecil)
@router.get("/", response_model=List[LogResponse])
def get_logs(limit: int = 50, db: Session = Depends(get_db)):

    rows = (
        db.query(ActivityLog)
        .order_by(desc(ActivityLog.created_at))
        .limit(limit)
        .all()
    )

    return [
        LogResponse(
            time=row.created_at.strftime("%H:%M"),
            type=row.type,
            text=row.message,
        )
        for row in rows
    ]


# CATAT LOG BARU - dipakai internal (misal dari sensors.py / devices.py)
# atau bisa dipanggil manual dari ESP32/skrip lain kalau perlu.
@router.post("/", status_code=201)
def create_log(payload: LogCreate, db: Session = Depends(get_db)):
    log = ActivityLog(type=payload.type, message=payload.message)
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"message": "Log tersimpan", "log_id": log.id}
