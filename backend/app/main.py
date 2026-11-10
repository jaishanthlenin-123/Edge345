"""
FastAPI Enterprise Backend Application
Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
Target: Raspberry Pi 5

Usage:
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Dict, Any, List, Optional

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="SG90 Servo Condition Monitoring API",
        description="Edge AI & Anomaly Detection Telemetry API for Raspberry Pi 5",
        version="1.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class RecordingStartRequest(BaseModel):
        session_name: str = "session_01"
        mode: str = "normal"

    from raspberry_pi.dashboard.server import ENGINE
    from raspberry_pi.database import get_recent_telemetry, get_recent_alerts, get_connection

    @app.get("/api/health")
    def health_check():
        return {"status": "healthy", "service": "servo_condition_monitoring"}

    @app.get("/api/status")
    def get_system_status():
        return {
            "system": ENGINE.system_status,
            "latest_prediction": ENGINE.latest_prediction
        }

    @app.get("/api/sensors/latest")
    def get_latest_sensor_data():
        return {
            "telemetry": ENGINE.latest_record,
            "prediction": ENGINE.latest_prediction,
            "connected": ENGINE.system_status["arduino_connected"]
        }

    @app.get("/api/sensors/history")
    def get_history(limit: int = 60):
        return get_recent_telemetry(limit=limit)

    @app.get("/api/servo/status")
    def get_servo_status():
        return {
            "angle": ENGINE.latest_record.get("servo_angle", 90),
            "current_a": ENGINE.latest_record.get("current_a", 0.0),
            "voltage_v": ENGINE.latest_record.get("voltage_v", 0.0)
        }

    @app.get("/api/anomalies")
    def get_anomalies(limit: int = 50):
        return get_recent_alerts(limit=limit)

    @app.get("/api/sessions")
    def get_sessions():
        conn = get_connection()
        rows = conn.execute("SELECT * FROM sessions ORDER BY start_time DESC LIMIT 20").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @app.post("/api/recording/start")
    def start_recording(req: RecordingStartRequest):
        sess_id = ENGINE.start_recording(session_name=req.session_name, mode=req.mode)
        return {"status": "started", "session_id": sess_id}

    @app.post("/api/recording/stop")
    def stop_recording():
        result = ENGINE.stop_recording()
        return result

    @app.get("/api/model/status")
    def get_model_status():
        return {
            "is_trained": ENGINE.model.is_trained,
            "model_type": ENGINE.model.model_type,
            "metadata": ENGINE.model.metadata
        }

    @app.get("/api/plc/status")
    def get_plc_status():
        return {
            "plc_enabled": ENGINE.system_status.get("plc_enabled", False),
            "commanded_angle": ENGINE.plc_bridge.get_commanded_angle() if ENGINE.plc_bridge else 90,
            "emergency_stop": ENGINE.plc_bridge.get_emergency_stop() if ENGINE.plc_bridge else False
        }

    @app.get("/api/mqtt/status")
    def get_mqtt_status():
        return {
            "mqtt_connected": ENGINE.mqtt_client.is_connected if ENGINE.mqtt_client else False,
            "published_messages": ENGINE.mqtt_client.published_messages_count if ENGINE.mqtt_client else 0,
            "broker": getattr(ENGINE.mqtt_client, "broker_host", "none") if ENGINE.mqtt_client else "none"
        }
else:
    # Fallback explanation if fastapi is not installed
    app = None
