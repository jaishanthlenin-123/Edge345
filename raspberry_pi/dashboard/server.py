#!/usr/bin/env python3
"""
Autonomous Telemetry Backend & Dashboard Server
Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
Target: Raspberry Pi 5

Description:
    Zero-dependency, multi-threaded REST & Static Web Server.
    Runs background USB serial data acquisition, sliding-window feature extraction,
    real-time machine learning anomaly inference, and SQLite persistence.
    Exposes REST APIs and serves the dark industrial monitoring dashboard.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import time
import queue
import datetime
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, List, Optional

# Project imports
from raspberry_pi.config import (
    SERIAL_BAUD_RATE,
    NORMAL_LIMITS,
    BASE_DIR,
    DATABASE_PATH,
    SAVED_MODELS_DIR
)
from raspberry_pi.serial_reader import SerialReader, find_serial_port
from raspberry_pi.feature_extraction import FeatureExtractor
from raspberry_pi.models.anomaly_detector import AnomalyDetectionModel
from raspberry_pi.database import (
    init_db,
    create_session,
    close_session,
    insert_telemetry_batch,
    insert_alert,
    get_recent_telemetry,
    get_recent_alerts,
    get_connection
)

STATIC_DIR = Path(__file__).resolve().parent / "static"


class TelemetryEngine:
    """Core state engine running background acquisition and real-time ML inference."""

    def __init__(self):
        self.reader = SerialReader()
        self.extractor = FeatureExtractor(window_size=10)
        self.model = AnomalyDetectionModel()

        # Try loading trained model if exists
        latest_model_path = SAVED_MODELS_DIR / "anomaly_model_latest.pkl"
        if latest_model_path.exists():
            try:
                self.model = AnomalyDetectionModel.load(latest_model_path)
                print(f"[MODEL] Loaded trained model: {latest_model_path}")
            except Exception as e:
                print(f"[MODEL] Could not load saved model ({e}). Using baseline detector.")

        # Singleton engine instance
        self.latest_record: Dict[str, Any] = {
            "host_timestamp": "",
            "timestamp_ms": 0,
            "sequence": 0,
            "servo_angle": 90,
            "voltage_v": 0.0,
            "current_a": 0.0,
            "accel_x": 350,
            "accel_y": 350,
            "accel_z": 350,
            "sound_rms": 0.0,
            "sound_p2p": 0
        }

        self.latest_prediction: Dict[str, Any] = {
            "status": "NORMAL",
            "anomaly_score": 0.0,
            "is_anomaly": False,
            "contributing_features": []
        }

        self.system_status = {
            "arduino_connected": False,
            "serial_port": None,
            "baud_rate": SERIAL_BAUD_RATE,
            "total_packets": 0,
            "is_recording": False,
            "active_session_id": None,
            "active_session_name": None,
            "recording_count": 0,
            "uptime_seconds": 0,
            "plc_enabled": False,
            "mqtt_connected": False
        }

        # Initialize Industrial PLC Modbus bridge
        self.plc_bridge = None
        try:
            from raspberry_pi.plc_bridge import ModbusPLCBridge
            self.plc_bridge = ModbusPLCBridge()
            self.plc_bridge.start_server_background()
            self.system_status["plc_enabled"] = True
            print(f"[PLC] Industrial Modbus TCP Bridge running on port {self.plc_bridge.port}")
        except Exception as e:
            print(f"[PLC] Modbus TCP Bridge not active: {e}")

        # Initialize Secure MQTT client
        self.mqtt_client = None
        try:
            from raspberry_pi.mqtt_client import SecureMQTTClient
            self.mqtt_client = SecureMQTTClient()
            if self.mqtt_client.connect(timeout_s=1.0):
                self.system_status["mqtt_connected"] = True
                print("[MQTT] Secure MQTT client connected")
            else:
                print("[MQTT] Secure MQTT broker not reachable at startup; daemon will reconnect")
        except Exception as e:
            print(f"[MQTT] Secure MQTT not active: {e}")

        self.start_time = time.time()
        self.active_session_id: Optional[str] = None
        self.session_record_count = 0
        self.last_alert_time = 0
        self.consecutive_overcurrent = 0
        self.running = True
        self.thread = threading.Thread(target=self._acquisition_loop, daemon=True)
        self.thread.start()

    def _acquisition_loop(self):
        """Continuous background thread reading from Arduino, running inference & persisting."""
        init_db()
        db_buffer = []

        while self.running:
            self.system_status["uptime_seconds"] = int(time.time() - self.start_time)
            self.system_status["arduino_connected"] = self.reader.is_connected
            self.system_status["serial_port"] = self.reader.port

            if not self.reader.is_connected:
                if not self.reader.connect():
                    time.sleep(1.5)
                    continue

            try:
                # Read line
                line = self.reader.ser.readline()
                if not line:
                    continue

                line_str = line.decode("utf-8", errors="replace").strip()
                record = self.reader.parse_line(line_str)
                if not record:
                    continue

                # Run feature extraction on sliding window
                features = self.extractor.update(record)
                if features:
                    pred = self.model.predict_window(features)
                    self.latest_prediction = pred
                    record["anomaly_score"] = pred["anomaly_score"]
                    record["is_anomaly"] = 1 if pred["is_anomaly"] else 0

                    now_time = time.time()
                    # Alert generation if anomalous (Rate-limited to once every 5 seconds)
                    if pred["is_anomaly"] and (now_time - self.last_alert_time > 5.0):
                        top_reasons = ", ".join(f"{k} (z={v})" for k, v in pred["contributing_features"])
                        insert_alert(
                            severity="WARNING" if pred["anomaly_score"] < 0.75 else "CRITICAL",
                            channel="MULTIVARIATE_ML",
                            message=f"Anomaly detected (Score: {pred['anomaly_score']:.2f}) -> Drivers: {top_reasons}",
                            reading=pred["anomaly_score"],
                            threshold=getattr(self.model, "threshold", 0.65),
                            session_id=self.active_session_id
                        )
                        self.last_alert_time = now_time
                else:
                    record["anomaly_score"] = 0.0
                    record["is_anomaly"] = 0

                # Check user threshold: immediately flag anomaly if current > 0.200A
                if record["current_a"] > NORMAL_LIMITS["current_max_a"]:
                    record["anomaly_score"] = 0.95
                    record["is_anomaly"] = 1
                    self.latest_prediction = {
                        "status": "ANOMALY",
                        "anomaly_score": 0.95,
                        "is_anomaly": True,
                        "contributing_features": [("current_exceeded_0.200A", round(record["current_a"], 3))]
                    }
                    if time.time() - self.last_alert_time > 3.0:
                        insert_alert(
                            severity="CRITICAL",
                            channel="CURRENT_OVERLOAD",
                            message=f"Current exceeded threshold: {record['current_a']:.3f}A > {NORMAL_LIMITS['current_max_a']}A",
                            reading=record["current_a"],
                            threshold=NORMAL_LIMITS["current_max_a"],
                            session_id=self.active_session_id
                        )
                        self.last_alert_time = time.time()

                self.latest_record = record
                self.system_status["total_packets"] = self.reader.total_packets_received

                # Sync to Industrial Modbus PLC Bridge
                if self.plc_bridge:
                    try:
                        self.plc_bridge.update_from_telemetry(record, self.latest_prediction)
                    except Exception:
                        pass

                # Publish to Secure MQTT Topics
                if self.mqtt_client and self.mqtt_client.is_connected:
                    try:
                        self.mqtt_client.publish_telemetry_frame(record, self.latest_prediction)
                        self.system_status["mqtt_connected"] = True
                    except Exception:
                        self.system_status["mqtt_connected"] = False

                # Database batch insertion
                db_buffer.append(record)
                if len(db_buffer) >= 5:
                    insert_telemetry_batch(db_buffer, session_id=self.active_session_id)
                    db_buffer.clear()

                if self.active_session_id:
                    self.session_record_count += 1
                    self.system_status["recording_count"] = self.session_record_count

            except Exception as e:
                time.sleep(0.5)

    def start_recording(self, session_name: str, mode: str = "normal") -> str:
        """Starts a named recording session."""
        self.active_session_id = create_session(session_name=session_name, mode=mode)
        self.session_record_count = 0
        self.system_status["is_recording"] = True
        self.system_status["active_session_id"] = self.active_session_id
        self.system_status["active_session_name"] = session_name
        self.system_status["recording_count"] = 0
        return self.active_session_id

    def stop_recording(self) -> Dict[str, Any]:
        """Stops active recording session."""
        if not self.active_session_id:
            return {"status": "error", "message": "No active recording session"}

        sess_id = self.active_session_id
        count = self.session_record_count
        close_session(sess_id, count)

        self.active_session_id = None
        self.system_status["is_recording"] = False
        self.system_status["active_session_id"] = None
        self.system_status["active_session_name"] = None

        return {"status": "ok", "session_id": sess_id, "records_saved": count}


# Singleton engine instance
ENGINE = TelemetryEngine()


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """Handles REST API and Static File delivery."""

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # REST API Routes
        if path == "/api/status":
            self._send_json({
                "system": ENGINE.system_status,
                "latest_prediction": ENGINE.latest_prediction
            })
            return

        elif path == "/api/sensors/latest":
            self._send_json({
                "telemetry": ENGINE.latest_record,
                "prediction": ENGINE.latest_prediction,
                "connected": ENGINE.system_status["arduino_connected"]
            })
            return

        elif path == "/api/sensors/history":
            history = get_recent_telemetry(limit=60)
            self._send_json(history)
            return

        elif path == "/api/anomalies":
            alerts = get_recent_alerts(limit=30)
            self._send_json(alerts)
            return

        elif path == "/api/plc/status":
            self._send_json({
                "plc_enabled": ENGINE.system_status["plc_enabled"],
                "commanded_angle": ENGINE.plc_bridge.get_commanded_angle() if ENGINE.plc_bridge else 90,
                "emergency_stop": ENGINE.plc_bridge.get_emergency_stop() if ENGINE.plc_bridge else False
            })
            return

        elif path == "/api/mqtt/status":
            self._send_json({
                "mqtt_connected": ENGINE.mqtt_client.is_connected if ENGINE.mqtt_client else False,
                "published_messages": ENGINE.mqtt_client.published_messages_count if ENGINE.mqtt_client else 0,
                "broker": getattr(ENGINE.mqtt_client, "broker_host", "none") if ENGINE.mqtt_client else "none"
            })
            return

        elif path == "/api/health":
            self._send_json({"status": "healthy", "time": datetime.datetime.now().isoformat()})
            return

        # Static File Routes (HTML, JS, CSS)
        if path == "/" or path == "/index.html":
            file_to_serve = STATIC_DIR / "index.html"
            content_type = "text/html; charset=utf-8"
        elif path.endswith(".js"):
            file_to_serve = STATIC_DIR / Path(path).name
            content_type = "application/javascript"
        elif path.endswith(".css"):
            file_to_serve = STATIC_DIR / Path(path).name
            content_type = "text/css"
        else:
            file_to_serve = None

        if file_to_serve and file_to_serve.exists():
            with open(file_to_serve, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404, "File Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length) if length > 0 else b"{}"

        try:
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            body = {}

        if path == "/api/recording/start":
            name = body.get("session_name", f"session_{int(time.time())}")
            mode = body.get("mode", "normal")
            sess_id = ENGINE.start_recording(session_name=name, mode=mode)
            self._send_json({"status": "recording_started", "session_id": sess_id})

        elif path == "/api/recording/stop":
            result = ENGINE.stop_recording()
            self._send_json(result)

        else:
            self.send_error(404, "Endpoint Not Found")


def run_dashboard_server(host: str = "0.0.0.0", port: int = 8000):
    """Starts the HTTP server."""
    server = ThreadingHTTPServer((host, port), DashboardRequestHandler)
    print("=" * 80)
    print(f" SERVO MONITORING DASHBOARD ONLINE")
    print(f" URL: http://localhost:{port} (or http://<RaspberryPi_IP>:{port})")
    print("=" * 80)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down dashboard server...")
        ENGINE.running = False
        server.server_close()


if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_dashboard_server(port=port_arg)
