"""
mqtt_client.py
Jembatan antara HiveMQ Cloud dan database backend.

DISESUAIKAN dengan firmware ESP32 "esp32-tani" yang publish tiap sensor
ke topic terpisah dengan payload TEKS POLOS (bukan JSON), contoh:
    sensor/soil       -> "38"
    sensor/suhu       -> "29.20"
    sensor/kelembaban -> "65.00"
    sensor/tegangan   -> "4.97"
    sensor/daya       -> "3.100"
    sensor/jarak      -> "120.50"
    sensor/status     -> "AMAN" / "HAMA"
    sensor/pompa      -> "ON" / "OFF"

Karena tiap sensor dikirim terpisah (bukan satu paket gabungan), backend
menyimpan "state terakhir" di memori (_latest), lalu setiap kali ada pesan
masuk, snapshot gabungan itu disimpan sebagai satu baris SensorReading baru.

Untuk kontrol arah sebaliknya (dashboard -> ESP32), backend publish teks
polos "ON"/"OFF" ke topic kontrol/pompa, kontrol/buzzer, atau kontrol/led
sesuai device_code yang diklik di halaman Actuators.
"""

import os
import ssl
import threading
from datetime import datetime

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

BROKER   = os.getenv("MQTT_BROKER", "")
PORT     = int(os.getenv("MQTT_PORT", "8883"))
USERNAME = os.getenv("MQTT_USERNAME", "")
PASSWORD = os.getenv("MQTT_PASSWORD", "")

# subscribe ke semua topic di bawah "sensor/" sekaligus
TOPIC_SENSOR_WILDCARD = "sensor/#"

# topic kontrol -> dipakai publish_command() berdasarkan device_code
TOPIC_KONTROL_POMPA  = "kontrol/pompa"
TOPIC_KONTROL_BUZZER = "kontrol/buzzer"
TOPIC_KONTROL_LED    = "kontrol/led"

# mapping device_code (di tabel `devices`) -> topic kontrol ESP32
# sesuaikan device_code ini dengan yang ada di database kamu (lihat seed.py / tabel devices)
DEVICE_TOPIC_MAP = {
    "dev003": TOPIC_KONTROL_POMPA,   # Pompa Air Mini DC
    "dev002": TOPIC_KONTROL_POMPA,   # Relay Module (kalau device yang diklik adalah relay-nya pompa)
    "dev007": TOPIC_KONTROL_BUZZER,  # Buzzer Alarm
    "dev008": TOPIC_KONTROL_LED,     # LED Indikator
}

# --------------------------------------------------------
# State koneksi - diekspos ke endpoint /mqtt/status
# --------------------------------------------------------
mqtt_status = {
    "connected": False,
    "broker": BROKER,
    "last_message_at": None,
    "error": None,
}

# --------------------------------------------------------
# State sensor terakhir - digabung jadi 1 snapshot tiap ada pesan masuk
# --------------------------------------------------------
_latest = {
    "soil_moisture": None,
    "air_temp": None,
    "air_humidity": None,       # kelembaban udara (tidak ada kolomnya di tabel saat ini, disimpan di memori saja)
    "pump_voltage": None,
    "pump_power": None,
    "distance_cm": None,        # jarak ultrasonic (tidak ada kolomnya di tabel saat ini)
    "ultrasonic_detected": False,
    "pump_on": False,
}

_client: "mqtt.Client | None" = None


# --------------------------------------------------------
# Callbacks
# --------------------------------------------------------

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        mqtt_status["connected"] = True
        mqtt_status["error"] = None
        print(f"[MQTT] Terhubung ke {BROKER}:{PORT}")
        client.subscribe(TOPIC_SENSOR_WILDCARD, qos=1)
        print(f"[MQTT] Subscribe ke: {TOPIC_SENSOR_WILDCARD}")
    else:
        codes = {
            1: "Versi protokol tidak didukung",
            2: "Client ID tidak valid",
            3: "Server tidak tersedia",
            4: "Username atau password salah",
            5: "Tidak diotorisasi",
        }
        mqtt_status["connected"] = False
        mqtt_status["error"] = codes.get(rc, f"Error kode {rc}")
        print(f"[MQTT] Gagal terhubung: {mqtt_status['error']}")


def on_disconnect(client, userdata, rc):
    mqtt_status["connected"] = False
    if rc != 0:
        print(f"[MQTT] Koneksi terputus, mencoba reconnect... (rc={rc})")
    else:
        print("[MQTT] Koneksi ditutup.")


def _safe_float(value: str):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def on_message(client, userdata, msg):
    """
    Dipanggil setiap kali ESP32 publish ke salah satu topic sensor/*.
    Payload berupa teks polos (bukan JSON), jadi di-parse manual sesuai topic.
    """
    topic = msg.topic
    payload_str = msg.payload.decode("utf-8", errors="ignore").strip()

    print(f"[MQTT] Data diterima dari {topic}: {payload_str}")
    mqtt_status["last_message_at"] = datetime.utcnow().isoformat()

    if topic == "sensor/soil":
        _latest["soil_moisture"] = _safe_float(payload_str)
    elif topic == "sensor/suhu":
        _latest["air_temp"] = _safe_float(payload_str)
    elif topic == "sensor/kelembaban":
        _latest["air_humidity"] = _safe_float(payload_str)
    elif topic == "sensor/tegangan":
        _latest["pump_voltage"] = _safe_float(payload_str)
    elif topic == "sensor/daya":
        _latest["pump_power"] = _safe_float(payload_str)
    elif topic == "sensor/jarak":
        _latest["distance_cm"] = _safe_float(payload_str)
    elif topic == "sensor/status":
        _latest["ultrasonic_detected"] = (payload_str == "HAMA")
    elif topic == "sensor/pompa":
        _latest["pump_on"] = (payload_str == "ON")
    else:
        # topic lain yang belum di-handle, abaikan saja
        return

    _save_snapshot()


def _save_snapshot():
    """
    Simpan gabungan state _latest saat ini sebagai satu baris SensorReading baru.
    Dipanggil setiap kali ada pesan sensor masuk (jadi akan ada beberapa baris
    mirip dalam rentang waktu dekat, itu wajar karena ESP32 publish per-sensor).
    """
    from app.database.database import SessionLocal
    from app.models.sensor_reading import SensorReading
    from app.models.log import ActivityLog

    voltage = _latest["pump_voltage"] or 0
    power   = _latest["pump_power"] or 0
    current = round(power / voltage, 3) if voltage else 0

    db = SessionLocal()
    try:
        reading = SensorReading(
            soil_moisture       = _latest["soil_moisture"],
            air_temp             = _latest["air_temp"],
            pump_voltage         = voltage,
            pump_current         = current,
            pump_power           = power,
            ultrasonic_detected = _latest["ultrasonic_detected"],
            pump_on               = _latest["pump_on"],
            air_humidity         = _latest["air_humidity"],
            distance_cm           = _latest["distance_cm"],
        )
        db.add(reading)

        if _latest["ultrasonic_detected"]:
            db.add(ActivityLog(
                type="warning",
                message="Hama/objek terdeteksi di area kebun (sensor ultrasonic)"
            ))

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[MQTT] Error menyimpan data ke database: {e}")
    finally:
        db.close()


# --------------------------------------------------------
# Fungsi publish perintah ke ESP32
# --------------------------------------------------------

def publish_command(device_code: str, command: str):
    """
    Dipanggil dari api/devices.py saat admin klik ON/OFF di dashboard.
    Payload dikirim TEKS POLOS ("ON"/"OFF"), sesuai yang di-expect callback()
    di firmware ESP32 (bukan JSON).
    """
    global _client

    if _client is None or not mqtt_status["connected"]:
        print("[MQTT] Tidak bisa publish - belum terhubung ke broker.")
        return False

    topic = DEVICE_TOPIC_MAP.get(device_code)
    if not topic:
        print(f"[MQTT] device_code '{device_code}' tidak ada di DEVICE_TOPIC_MAP, publish dilewati.")
        return False

    result = _client.publish(topic, command, qos=1)

    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"[MQTT] Perintah {command} dikirim ke {topic}")
        return True
    else:
        print(f"[MQTT] Gagal publish ke {topic}: rc={result.rc}")
        return False


# --------------------------------------------------------
# Start MQTT (dipanggil dari main.py saat startup)
# --------------------------------------------------------

def start_mqtt():
    global _client

    if not BROKER:
        print("[MQTT] MQTT_BROKER kosong di .env, MQTT tidak dijalankan.")
        return

    client_id = f"GardenTechBackend-{os.getpid()}"
    _client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)

    _client.tls_set(
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLS_CLIENT,
    )
    _client.tls_insecure_set(False)

    _client.username_pw_set(USERNAME, PASSWORD)

    _client.on_connect    = on_connect
    _client.on_disconnect = on_disconnect
    _client.on_message    = on_message

    _client.reconnect_delay_set(min_delay=2, max_delay=30)

    try:
        _client.connect(BROKER, PORT, keepalive=60)
    except Exception as e:
        mqtt_status["error"] = str(e)
        print(f"[MQTT] Gagal memulai koneksi: {e}")
        return

    thread = threading.Thread(target=_client.loop_forever, daemon=True)
    thread.start()
    print(f"[MQTT] Client berjalan di background thread (PID {os.getpid()})")