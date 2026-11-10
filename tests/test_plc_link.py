#!/usr/bin/env python3
"""
Unit and Integration Tests for Category 06: Industrial PLC Modbus TCP Link
Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
Target: Raspberry Pi 5 to PLC (Siemens / Schneider / Allen-Bradley) Interface
"""

import sys
import time
import pytest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from raspberry_pi.plc_bridge import ModbusPLCBridge, PLCClientDemo


class TestPLCModbusLink:
    """Verifies Modbus TCP server, register mapping, scaling, and bidirectional communication."""

    @classmethod
    def setup_class(cls):
        """Starts background Modbus TCP server on test port 5025."""
        cls.test_port = 5025
        cls.bridge = ModbusPLCBridge(host="127.0.0.1", port=cls.test_port, slave_id=1)
        cls.bridge.start_server_background()
        time.sleep(0.8)  # Allow socket bind

    def test_plc_connection_and_initial_telemetry(self):
        """Tests that a PLC client connects and reads default scaled input registers."""
        client = PLCClientDemo(host="127.0.0.1", port=self.test_port, slave_id=1)
        assert client.connect() is True, "Failed to connect to Modbus TCP server"

        data = client.read_telemetry()
        assert "servo_angle_deg" in data
        assert data["servo_angle_deg"] == 90
        assert data["voltage_v"] == pytest.approx(5.00, rel=1e-2)
        assert data["current_a"] == pytest.approx(0.092, rel=1e-2)
        assert data["accel_x"] == 335
        assert data["accel_y"] == 392
        assert data["accel_z"] == 307
        assert data["sound_rms"] == pytest.approx(16.0, rel=1e-1)
        assert data["sound_p2p"] == 65
        assert data["anomaly_score"] == 0.0

        client.disconnect()

    def test_dynamic_telemetry_update_and_scaling(self):
        """Verifies real-time floating-point updates correctly map into 16-bit integer registers."""
        client = PLCClientDemo(host="127.0.0.1", port=self.test_port, slave_id=1)
        client.connect()

        # Update bridge with new dynamic readings
        test_record = {
            "servo_angle": 150,
            "voltage_v": 4.96,
            "current_a": 0.138,
            "accel_x": 345,
            "accel_y": 380,
            "accel_z": 315,
            "sound_rms": 24.5,
            "sound_p2p": 88,
            "sequence": 502
        }
        test_pred = {
            "status": "NORMAL",
            "anomaly_score": 0.15,
            "is_anomaly": False
        }
        self.bridge.update_from_telemetry(test_record, test_pred)
        time.sleep(0.1)

        data = client.read_telemetry()
        assert data["servo_angle_deg"] == 150
        assert data["voltage_v"] == pytest.approx(4.96, rel=1e-2)
        assert data["current_a"] == pytest.approx(0.138, rel=1e-2)
        assert data["accel_x"] == 345
        assert data["sound_rms"] == pytest.approx(24.5, rel=1e-1)
        assert data["sound_p2p"] == 88
        assert data["anomaly_score"] == pytest.approx(0.15, rel=1e-2)
        assert data["packets_total"] == 502

        client.disconnect()

    def test_plc_command_write_holding_registers(self):
        """Tests PLC supervisory write: commanding servo target angle via Holding Register 3."""
        client = PLCClientDemo(host="127.0.0.1", port=self.test_port, slave_id=1)
        client.connect()

        write_success = client.write_commanded_angle(135)
        assert write_success is True, "Modbus FC 06 write to Holding Register failed"
        time.sleep(0.1)

        read_back_angle = self.bridge.get_commanded_angle()
        assert read_back_angle == 135, f"Expected 135 deg, got {read_back_angle}"

        client.disconnect()

    def test_plc_emergency_stop_coil(self):
        """Tests safety interlock: triggering and resetting Emergency Stop via Coil 0."""
        client = PLCClientDemo(host="127.0.0.1", port=self.test_port, slave_id=1)
        client.connect()

        # Trigger E-stop
        assert client.write_emergency_stop(True) is True
        time.sleep(0.1)
        assert self.bridge.get_emergency_stop() is True, "Emergency stop should be active"

        # Reset E-stop
        assert client.write_emergency_stop(False) is True
        time.sleep(0.1)
        assert self.bridge.get_emergency_stop() is False, "Emergency stop should be cleared"

        client.disconnect()

