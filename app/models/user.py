"""
models/user.py
Tabel 'users' - menyimpan akun login dashboard.
Field disesuaikan dengan frontend (username + password + role),
BUKAN fullname/email seperti contoh dosen.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import TIMESTAMP
from sqlalchemy.sql import func

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(50), unique=True, nullable=False, index=True)

    password_hash = Column(String(255), nullable=False)

    # role cuma dua pilihan: "Admin" atau "Viewer" (sesuai frontend)
    role = Column(String(20), nullable=False, default="Viewer")

    is_active = Column(Boolean, default=True)

    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )
