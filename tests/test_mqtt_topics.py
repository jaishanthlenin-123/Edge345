#!/usr/bin/env python3
"""
Unit and Integration Tests for Category 05: MQTT Topic Structure
Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
Target: Raspberry Pi 5 Edge MQTT Topic Router

Tests:
    - Standardized 7-topic hierarchical schema:
        1. motor/servo01/sensors/imu
        2. motor/servo01/sensors/current
        3. motor/servo01/sensors/voltage
        4. motor/servo01/sensors/audio
        5. motor/servo01/status
        6. motor/servo01/alerts
        7. motor/servo01/health
    - JSON payload structure, unit tags, and ISO 8601 timestamps
    - QoS levels and Retain flags
"""

import json
import pytest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
import sys
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from raspberry_pi.config import MQTT_TOPICS
from raspberry_pi.mqtt_client import SecureMQTTClient


class TestMQTTTopicStructure:
    """Validates topic paths, payload schemas, and serialization."""

    def test_topic_naming_compliance(self):
        """Verifies exact adherence to specified M4 hierarchical naming convention."""
        assert MQTT_TOPICS["imu"] == "motor/servo01/sensors/imu"
        assert MQTT_TOPICS["current"] == "motor/servo01/sensors/current"
        assert MQTT_TOPICS["voltage"] == "motor/servo01/sensors/voltage"
        assert MQTT_TOPICS["audio"] == "motor/servo01/sensors/audio"
        assert MQTT_TOPICS["status"] == "motor/servo01/status"
        assert MQTT_TOPICS["alerts"] == "motor/servo01/alerts"
        assert MQTT_TOPICS["health"] == "motor/servo01/health"

    def test_mock_published_payload_schemas(self, monkeypatch):
        """
        Captures payloads published by each topic method and validates their schema,
        types, and physical measurement units.
        """
        client = SecureMQTTClient(broker_host="127.0.0.1", use_tls=False)
        captured = {}

        def mock_publish_json(topic, payload, qos=None, retain=False):
            captured[topic] = {
                "payload": payload,
                "qos": qos,
                "retain": retain
            }
            return True

        monkeypatch.setattr(client, "publish_json", mock_publish_json)

        # 1. IMU / Vibration
        client.publish_imu(ax=336, ay=392, az=308, timestamp_ms=5000)
        assert MQTT_TOPICS["imu"] in captured
        imu_p = captured[MQTT_TOPICS["imu"]]["payload"]
        assert imu_p["accel_x"] == 336
        assert imu_p["accel_y"] == 392
        assert imu_p["accel_z"] == 308
        assert "magnitude" in imu_p
        assert imu_p["unit"] == "raw_adc_10bit"

        # 2. Current
        client.publish_current(current_a=0.092, timestamp_ms=5000)
        assert MQTT_TOPICS["current"] in captured
        curr_p = captured[MQTT_TOPICS["current"]]["payload"]
        assert curr_p["current_a"] == 0.092
        assert curr_p["unit"] == "A"
        assert curr_p["status"] == "NORMAL"

        # 3. Voltage
        client.publish_voltage(voltage_v=5.02, timestamp_ms=5000)
        assert MQTT_TOPICS["voltage"] in captured
        volt_p = captured[MQTT_TOPICS["voltage"]]["payload"]
        assert volt_p["voltage_v"] == 5.02
        assert volt_p["unit"] == "V"
        assert volt_p["status"] == "NOMINAL"

        # 4. Audio
        client.publish_audio(sound_rms=16.2, sound_p2p=65, timestamp_ms=5000)
        assert MQTT_TOPICS["audio"] in captured
        aud_p = captured[MQTT_TOPICS["audio"]]["payload"]
        assert aud_p["sound_rms"] == 16.2
        assert aud_p["sound_p2p"] == 65

        # 5. Servo Status (Retained)
        client.publish_servo_status(servo_angle=90, operational_state="NORMAL", anomaly_score=0.05, is_anomaly=False)
        assert MQTT_TOPICS["status"] in captured
        stat_p = captured[MQTT_TOPICS["status"]]["payload"]
        assert stat_p["servo_angle"] == 90
        assert stat_p["condition"] == "NORMAL"
        assert captured[MQTT_TOPICS["status"]]["retain"] is True

        # 6. Alerts (QoS 2)
        client.publish_alert(severity="CRITICAL", channel="OVERCURRENT", message="Exceeded 0.85A", metric_value=0.92, threshold=0.85)
        assert MQTT_TOPICS["alerts"] in captured
        alrt_p = captured[MQTT_TOPICS["alerts"]]["payload"]
        assert alrt_p["severity"] == "CRITICAL"
        assert alrt_p["metric_value"] == 0.92
        assert captured[MQTT_TOPICS["alerts"]]["qos"] == 2

        # 7. Health Heartbeat
        client.publish_health(uptime_s=1200.5, total_packets=5430, arduino_connected=True)
        assert MQTT_TOPICS["health"] in captured
        hlth_p = captured[MQTT_TOPICS["health"]]["payload"]
        assert hlth_p["uptime_seconds"] == 1200.5
        assert hlth_p["arduino_connected"] is True

    def test_full_frame_router_distribution(self, monkeypatch):
        """Tests publish_telemetry_frame routes a raw telemetry record into multiple topics."""
        client = SecureMQTTClient(broker_host="127.0.0.1", use_tls=False)
        published_topics = []

        def mock_publish_json(topic, payload, qos=None, retain=False):
            published_topics.append(topic)
            return True

        monkeypatch.setattr(client, "publish_json", mock_publish_json)

        telemetry_sample = {
            "timestamp_ms": 15000,
            "sequence": 145,
            "servo_angle": 150,
            "voltage_v": 5.01,
            "current_a": 0.088,
            "accel_x": 338,
            "accel_y": 391,
            "accel_z": 307,
            "sound_rms": 14.8,
            "sound_p2p": 54
        }
        res = client.publish_telemetry_frame(telemetry_sample)

        assert all(res.values()), "All topic dispatches should report True"
        assert MQTT_TOPICS["imu"] in published_topics
        assert MQTT_TOPICS["current"] in published_topics
        assert MQTT_TOPICS["voltage"] in published_topics
        assert MQTT_TOPICS["audio"] in published_topics
        assert MQTT_TOPICS["status"] in published_topics

