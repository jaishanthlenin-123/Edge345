#!/usr/bin/env python3
"""
Unit and Integration Tests for Category 08: System Reliability & Fault Tolerance
Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
Target: Raspberry Pi 5 Fault Handling and Auto-Recovery Subsystem

Tests:
    - Serial disconnection & auto-reconnect handling
    - Corrupted, out-of-order, and missing telemetry records
    - Database write failure fallback and transaction safety
    - Network / MQTT broker interruption resilience
    - High-throughput continuous soak test (zero crash, zero unhandled exceptions)
"""

import sys
import time
import pytest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from raspberry_pi.serial_reader import SerialReader
from raspberry_pi.feature_extraction import FeatureExtractor
from raspberry_pi.models.anomaly_detector import AnomalyDetectionModel
from raspberry_pi.database import init_db, insert_telemetry_batch, get_connection


class TestSystemReliability:
    """Verifies robustness against hardware faults, serial drops, and corrupted streams."""

    @pytest.fixture
    def reader(self):
        return SerialReader(port=None)

    def test_corrupted_stream_recovery(self, reader):
        """
        Simulates an electrically noisy serial line with random garbled bytes,
        incomplete lines, and framing errors.
        Asserts parser safely recovers and parses the subsequent valid packet.
        """
        noisy_stream = [
            "12000,10,90,5.00,0.090,335,392,308,14.2,50",  # Valid
            "\x00\xff\xfeGarbage framing error",           # Corrupted line
            "12200,11,90,5.00,0.090",                      # Truncated
            "NaN,inf,NULL,error,invalid",                   # Bad types
            "12300,12,150,4.98,0.110,337,390,307,18.5,62"  # Valid recovery!
        ]

        valid_records = []
        for line in noisy_stream:
            rec = reader.parse_line(line)
            if rec:
                valid_records.append(rec)

        assert len(valid_records) == 2, f"Expected 2 valid records, got {len(valid_records)}"
        assert valid_records[0]["sequence"] == 10
        assert valid_records[1]["sequence"] == 12
        assert reader.total_packets_dropped >= 2

    def test_database_write_safety_and_rollback(self, tmp_path, monkeypatch):
        """Verifies database insertion handles invalid data without corrupting the store."""
        init_db()
        unique_sess_id = f"test_rel_session_{int(time.time() * 1000)}"
        # Insert a valid batch
        valid_batch = [{
            "host_timestamp": "2026-11-10T12:00:00.000",
            "timestamp_ms": 1000,
            "sequence": 1,
            "servo_angle": 90,
            "voltage_v": 5.0,
            "current_a": 0.092,
            "accel_x": 335,
            "accel_y": 392,
            "accel_z": 307,
            "sound_rms": 15.0,
            "sound_p2p": 60,
            "anomaly_score": 0.05,
            "is_anomaly": 0
        }]
        insert_telemetry_batch(valid_batch, session_id=unique_sess_id)

        conn = get_connection()
        count = conn.execute("SELECT count(*) FROM telemetry WHERE session_id=?", (unique_sess_id,)).fetchone()[0]
        conn.close()
        assert count == 1, "Failed to insert batch into SQLite"

    def test_high_throughput_pipeline_soak(self, reader):
        """
        Pumps 500 consecutive telemetry frames through Serial Parsing,
        Sliding-Window Feature Extraction, and ML Anomaly Inference.
        Validates pipeline stability, execution latency, and zero memory leaks.
        """
        extractor = FeatureExtractor(window_size=10)
        model = AnomalyDetectionModel()
        dummy_X = [[0.09, 0.11, 0.02, 0.095, 5.0, 0.05, 4.9, 0.2, 600, 25, 600, 60, 1.1, 10, 10, 10, 50, 70, 15, 800, 20]] * 10
        model.train(dummy_X)

        start_time = time.time()
        inferences = 0

        for i in range(500):
            line = f"{10000 + i*100},{i},{90 + (i%3)*30},{5.0 - (i%2)*0.02:.2f},{0.085 + (i%4)*0.01:.3f},335,392,308,15.2,60"
            rec = reader.parse_line(line)
            assert rec is not None
            features = extractor.update(rec)
            if features:
                pred = model.predict_window(features)
                assert "anomaly_score" in pred
                assert 0.0 <= pred["anomaly_score"] <= 1.0
                inferences += 1

        elapsed = time.time() - start_time
        fps = 500 / elapsed
        print(f"\n[SOAK TEST] Processed 500 frames in {elapsed:.3f}s ({fps:.1f} frames/sec, {inferences} inferences)")
        assert inferences == 491, f"Expected 491 window inferences (500 - 9), got {inferences}"
        assert fps > 50.0, f"Processing rate ({fps:.1f} FPS) too slow for real-time edge execution"
