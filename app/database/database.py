"""
database.py
Konfigurasi koneksi ke database MySQL (dikelola via phpMyAdmin / XAMPP / Laragon).
Polanya sama seperti contoh dosen (SQLAlchemy + sessionmaker),
hanya driver-nya diganti dari PostgreSQL (psycopg2) ke MySQL (PyMySQL).
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "smart_garden_db")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Format URL koneksi MySQL untuk SQLAlchemy + PyMySQL
# mysql+pymysql://user:password@host:port/nama_database
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # cek koneksi masih hidup sebelum dipakai (penting untuk MySQL)
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    """Dependency FastAPI: buka session DB per-request, otomatis ditutup setelah selesai."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
