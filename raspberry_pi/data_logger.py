#!/usr/bin/env python3
"""
Structured Telemetry Data Logger & Session Manager
Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
Target: Raspberry Pi 5

Description:
    Records validated sensor records to CSV files and SQLite database.
    Organizes records by session type (normal, test, raw).
"""

import sys
import time
import datetime
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from typing import Optional, List, Dict, Any

from raspberry_pi.config import (
    RAW_DATA_DIR,
    NORMAL_DATA_DIR,
    TEST_DATA_DIR,
    TELEMETRY_COLUMNS
)
from raspberry_pi.serial_reader import SerialReader
from raspberry_pi.database import (
    init_db,
    create_session,
    close_session,
    insert_telemetry_batch
)


class DataLogger:
    """Manages simultaneous writing to CSV and SQLite with batch buffering."""

    def __init__(self, mode: str = "normal", output_path: Optional[Path] = None, session_name: Optional[str] = None):
        self.mode = mode.lower()
        self.session_name = session_name if session_name else f"servo_{self.mode}"
        
        # Determine CSV destination
        if output_path:
            self.file_path = Path(output_path)
        else:
            ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            target_dir = {
                "normal": NORMAL_DATA_DIR,
                "test": TEST_DATA_DIR
            }.get(self.mode, RAW_DATA_DIR)
            self.file_path = target_dir / f"{self.session_name}_{ts_str}.csv"

        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_handle = None
        self.records_logged = 0
        self.session_id: Optional[str] = None
        self.db_buffer: List[Dict[str, Any]] = []

    def open(self):
        """Initializes database session and opens CSV output."""
        init_db()
        self.session_id = create_session(session_name=self.session_name, mode=self.mode)
        self.file_handle = open(self.file_path, "w", buffering=1, encoding="utf-8")
        header = "host_timestamp," + ",".join(TELEMETRY_COLUMNS) + "\n"
        self.file_handle.write(header)

    def write_record(self, record: dict):
        """Appends record to CSV and buffers for database insertion."""
        if not self.file_handle:
            self.open()

        row = [
            str(record["host_timestamp"]),
            str(record["timestamp_ms"]),
            str(record.get("sequence", self.records_logged)),
            str(record["servo_angle"]),
            f"{record['voltage_v']:.2f}",
            f"{record['current_a']:.3f}",
            str(record["accel_x"]),
            str(record["accel_y"]),
            str(record["accel_z"]),
            f"{record.get('sound_rms', 0.0):.2f}",
            str(record.get("sound_p2p", 0))
        ]
        self.file_handle.write(",".join(row) + "\n")
        self.records_logged += 1

        self.db_buffer.append(record)
        if len(self.db_buffer) >= 10:
            self.flush_db()

    def flush_db(self):
        """Flushes buffered records to SQLite."""
        if self.db_buffer and self.session_id:
            try:
                insert_telemetry_batch(self.db_buffer, session_id=self.session_id)
            except Exception as e:
                print(f"\n[WARN] DB insert error: {e}")
            self.db_buffer.clear()

    def close(self):
        """Flushes remaining records, closes files, and marks session complete."""
        self.flush_db()
        if self.file_handle:
            self.file_handle.flush()
            self.file_handle.close()
            self.file_handle = None
        if self.session_id:
            close_session(self.session_id, self.records_logged)


def collect_dataset(mode: str = "normal", duration_s: int = 30, port: Optional[str] = None):
    """Executes a timed data collection run."""
    reader = SerialReader(port=port)
    logger = DataLogger(mode=mode)
    logger.open()

    print("=" * 80)
    print(f" DATASET COLLECTION: Mode='{mode.upper()}' | Duration={duration_s}s")
    print(f" CSV Target: {logger.file_path.resolve()}")
    print(f" Session ID: {logger.session_id}")
    print("=" * 80)

    start_time = time.time()
    last_packet_time = time.time()
    try:
        for record in reader.read_stream():
            last_packet_time = time.time()
            elapsed = time.time() - start_time
            logger.write_record(record)

            print(f"\r[{elapsed:>5.1f}s / {duration_s}s] "
                  f"Angle: {record['servo_angle']:>3}° | "
                  f"Volt: {record['voltage_v']:>4.2f}V | "
                  f"Curr: {record['current_a']:>5.3f}A | "
                  f"Accel: ({record['accel_x']:>3},{record['accel_y']:>3},{record['accel_z']:>3}) | "
                  f"Sound P2P: {record.get('sound_p2p', 0):>3} | "
                  f"Saved: {logger.records_logged}", end="", flush=True)

            if duration_s > 0 and elapsed >= duration_s:
                print(f"\n\n[COMPLETED] Reached duration limit ({duration_s}s).")
                break

            if time.time() - last_packet_time > 8.0:
                print("\n[WAIT] Waiting for incoming CSV telemetry from Arduino...")
                last_packet_time = time.time()

    except KeyboardInterrupt:
        print("\n\n[USER] Stopped by user.")
    finally:
        reader.close()
        logger.close()
        print(f"[SUMMARY] Total records saved: {logger.records_logged}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Collect Telemetry Dataset from Arduino Uno")
    parser.add_argument("--mode", type=str, default="normal", choices=["normal", "test", "raw"])
    parser.add_argument("--duration", type=int, default=30, help="Duration in seconds (default: 30)")
    parser.add_argument("--port", type=str, default=None)

    args = parser.parse_args()
    collect_dataset(mode=args.mode, duration_s=args.duration, port=args.port)
