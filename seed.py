"""
seed.py
Jalankan SEKALI setelah tabel database dibuat, untuk mengisi data awal:
- 6 device default (sesuai daftar komponen project: ESP32, relay, pompa,
  soil moisture, DHT22, ultrasonic)
- 1 akun admin default (username: admin, password: admin123)
- 1 baris pump_settings default

Cara pakai:
    python seed.py

Aman dijalankan berkali-kali — kalau datanya sudah ada, tidak akan
membuat duplikat.
"""

from app.database.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.device import Device
from app.models.pump_setting import PumpSetting
from app.core.security import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # ---------- akun admin default ----------
    existing_admin = db.query(User).filter(User.username == "admin").first()
    if not existing_admin:
        admin = User(
            username="admin",
            password_hash=hash_password("admin123"),
            role="Admin",
            is_active=True,
        )
        db.add(admin)
        print("Akun admin default dibuat (username: admin, password: admin123)")
    else:
        print("Akun admin sudah ada, dilewati.")

    # ---------- device default ----------
    default_devices = [
        {"device_code": "dev001", "name": "ESP32 DevKit V1", "type": "sensor", "is_online": True},
        {"device_code": "dev002", "name": "Relay Module 1CH", "type": "actuator", "is_online": True},
        {"device_code": "dev003", "name": "Pompa Air Mini DC", "type": "actuator", "is_online": True},
        {"device_code": "dev004", "name": "Soil Moisture Sensor", "type": "sensor", "is_online": True},
        {"device_code": "dev005", "name": "DHT22", "type": "sensor", "is_online": True},
        {"device_code": "dev006", "name": "Sensor Ultrasonic", "type": "sensor", "is_online": False},
        {"device_code": "dev007", "name": "Buzzer Alarm", "type": "actuator", "is_online": True},
        {"device_code": "dev008", "name": "LED Indikator", "type": "actuator", "is_online": True},
    ]

    for d in default_devices:
        exists = db.query(Device).filter(Device.device_code == d["device_code"]).first()
        if not exists:
            db.add(Device(**d))
            print(f"Device {d['device_code']} ({d['name']}) ditambahkan.")

    # ---------- pengaturan pompa default ----------
    existing_setting = db.query(PumpSetting).first()
    if not existing_setting:
        db.add(PumpSetting(auto_mode=True, threshold_percent=40.0))
        print("Pengaturan pompa default dibuat (auto_mode=True, threshold=40%).")

    db.commit()
    print("\nSeeding selesai.")

except Exception as e:
    db.rollback()
    print("Terjadi error saat seeding:", e)

finally:
    db.close()