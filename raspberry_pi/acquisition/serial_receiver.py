#!/usr/bin/env python3
"""
Live Telemetry Terminal Monitor
Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
Target: Raspberry Pi 5

Usage:
    ./run_servo_test.sh
    python3 raspberry_pi/acquisition/serial_receiver.py [--duration 30]
"""

import sys
import time
import argparse
import datetime
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from raspberry_pi.serial_reader import SerialReader
from raspberry_pi.data_logger import DataLogger


def run_live_monitor(args):
    reader = SerialReader(port=args.port, baud_rate=args.baud)
    logger = None
    if not args.no_log:
        logger = DataLogger(mode="raw", output_path=args.output)
        logger.open()
        print(f"[STORAGE] Logging live telemetry to: {logger.file_path.resolve()}")

    print("=" * 105)
    print(" SG90 SERVO MOTOR CONDITION MONITORING - LIVE TELEMETRY TERMINAL")
    print("=" * 105)
    print(f" {'TIME':<8} | {'SEQ':<5} | {'ANGLE':<5} | {'ACCEL (X, Y, Z)':<18} | {'CURRENT':<9} | {'VOLTAGE':<9} | {'MIC (P2P)':<11} | {'STATUS'}")
    print("-" * 105)

    start_time = time.time()
    try:
        for record in reader.read_stream():
            elapsed = time.time() - start_time
            if logger:
                logger.write_record(record)

            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            seq = record.get("sequence", 0)
            angle = record.get("servo_angle", 90)
            ax, ay, az = record.get("accel_x", 0), record.get("accel_y", 0), record.get("accel_z", 0)
            curr = record.get("current_a", 0.0)
            volt = record.get("voltage_v", 0.0)
            mic_p2p = record.get("sound_p2p", record.get("sound_raw", 0))

            accel_str = f"({ax:>3},{ay:>3},{az:>3})"
            curr_str = f"{curr:>5.3f}A"
            volt_str = f"{volt:>5.2f}V"
            mic_str = f"{mic_p2p:>4}"
            status = "OK"

            print(f" {now_str:<8} | {seq:<5} | {angle:>3}°  | {accel_str:<18} | {curr_str:<9} | {volt_str:<9} | {mic_str:<11} | {status}")

            if args.duration > 0 and elapsed >= args.duration:
                print(f"\n[DONE] Specified test duration of {args.duration}s reached.")
                break

    except KeyboardInterrupt:
        print("\n\n[USER] Stopped monitoring.")
    finally:
        reader.close()
        if logger:
            logger.close()
            print(f"[STORAGE] Closed dataset file ({logger.records_logged} records saved).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live Terminal Telemetry Monitor")
    parser.add_argument("--port", type=str, default=None, help="Serial port (default: auto-detect)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("--duration", type=int, default=0, help="Duration in seconds (0 = indefinite)")
    parser.add_argument("--output", type=str, default=None, help="Custom output CSV path")
    parser.add_argument("--no-log", action="store_true", help="Disable CSV logging")

    parsed_args = parser.parse_args()
    run_live_monitor(parsed_args)
