#!/usr/bin/env python3
"""
Unit and Integration Tests for Category 01: Sensor Data Acquisition
Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
Target: Arduino Uno to Raspberry Pi 5 Telemetry Interface
"""

import sys
import pytest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from raspberry_pi.serial_reader import SerialReader
from raspberry_pi.config import TELEMETRY_COLUMNS, NORMAL_LIMITS


class TestSensorDataAcquisition:
    """Verifies parsing, electrical bounds, and packet integrity for all sensors."""

    @pytest.fixture
    def reader(self):
        return SerialReader(port=None)

    def test_standard_10_field_csv_parsing(self, reader):
        """Verifies parsing of standard 10-field Arduino Uno CSV telemetry."""
        sample_line = "12450,42,90,5.02,0.092,336,392,308,16.22,65"
        record = reader.parse_line(sample_line)

        assert record is not None, "Failed to parse standard 10-field telemetry line"
        assert record["timestamp_ms"] == 12450
        assert record["sequence"] == 42
        assert record["servo_angle"] == 90
        assert record["voltage_v"] == pytest.approx(5.02, rel=1e-2)
        assert record["current_a"] == pytest.approx(0.092, rel=1e-2)
        assert record["accel_x"] == 336
        assert record["accel_y"] == 392
        assert record["accel_z"] == 308
        assert record["sound_rms"] == pytest.approx(16.22, rel=1e-2)
        assert record["sound_p2p"] == 65
        assert record["format"] == "standard_10col"
        assert reader.total_packets_received == 1
        assert reader.total_packets_dropped == 0

    def test_sensor_physical_ranges(self, reader):
        """Verifies sensor readings are within physical hardware operational limits."""
        # Simulated normal dynamic cycle sample
        sample_line = "15000,43,150,4.98,0.115,340,388,312,22.40,95"
        record = reader.parse_line(sample_line)

        # 1. Supply Voltage (0-25V divider, 5V nominal)
        assert NORMAL_LIMITS["voltage_min_v"] <= record["voltage_v"] <= NORMAL_LIMITS["voltage_max_v"]

        # 2. Motor Current (ACS712 5A module: nominal free motion < 0.200A)
        assert 0.0 <= record["current_a"] <= 1.50

        # 3. 3-Axis Accelerometer (10-bit ADC: 0-1023)
        for ax_name in ("accel_x", "accel_y", "accel_z"):
            val = record[ax_name]
            assert 0 <= val <= 1023, f"{ax_name} value {val} out of 10-bit ADC bounds"

        # 4. Microphone (MAX9814 Audio: RMS > 0, P2P in 0-1023)
        assert record["sound_rms"] >= 0.0
        assert 0 <= record["sound_p2p"] <= 1023

    def test_corrupted_and_truncated_packet_handling(self, reader):
        """Verifies reader drops invalid packets without crashing."""
        # Truncated packet (only 6 fields)
        corrupted_1 = "12450,42,90,5.02,0.092,336"
        res1 = reader.parse_line(corrupted_1)
        assert res1 is None

        # Non-numeric garbage
        corrupted_2 = "12450,42,BAD_ANGLE,5.02,NAN,336,392,308,16.22,65"
        res2 = reader.parse_line(corrupted_2)
        assert res2 is None
        assert reader.total_packets_dropped > 0

    def test_live_recorded_dataset_integrity(self):
        """Verifies real recorded dataset file conforms to standard schema."""
        dataset_path = PROJECT_ROOT / "datasets" / "normal" / "servo_normal_20261106_143433.csv"
        assert dataset_path.exists(), f"Recorded dataset missing: {dataset_path}"

        import csv
        with open(dataset_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) > 0, "Recorded dataset contains no rows"
        for col in TELEMETRY_COLUMNS:
            assert col in rows[0], f"Expected column {col} missing from recorded dataset"

        # Check sequence continuity
        seqs = [int(r["sequence"]) for r in rows]
        assert seqs == sorted(seqs), "Sequence numbers must be monotonically non-decreasing"

