"""
models/log.py
Tabel 'activity_logs' - catatan aktivitas sistem (penyiraman dimulai/berhenti,
objek terdeteksi, dll), ditampilkan di halaman Logs & cuplikan di Dashboard.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import TIMESTAMP
from sqlalchemy.sql import func

from app.database.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)

    # tipe log: "info", "success", "warning", "danger" (dipakai untuk warna badge di frontend)
    type = Column(String(20), nullable=False, default="info")

    message = Column(String(255), nullable=False)

    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        index=True
    )
