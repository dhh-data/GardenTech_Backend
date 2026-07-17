"""
api/mqtt.py
Endpoint status koneksi MQTT — dipakai frontend untuk update
indikator "MQTT terhubung / terputus" di topbar secara real-time.
"""

from fastapi import APIRouter
from app.mqtt_client import mqtt_status, publish_command

router = APIRouter(
    prefix="/mqtt",
    tags=["MQTT"]
)


@router.get("/status")
def get_mqtt_status():
    """
    Dicek frontend setiap beberapa detik.
    Response: { connected, broker, last_message_at, error }
    """
    return mqtt_status


@router.post("/publish")
def manual_publish(device_code: str, command: str):
    """
    Endpoint debug — publish perintah manual tanpa lewat /devices/{code}/command.
    Berguna saat testing koneksi MQTT dari Swagger UI.
    """
    success = publish_command(device_code, command)
    return {
        "success": success,
        "topic": f"gardenkit/{device_code}/control",
        "command": command,
    }
