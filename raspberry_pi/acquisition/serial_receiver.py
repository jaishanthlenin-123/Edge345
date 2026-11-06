#!/usr/bin/env python3
"""
Serial Data Acquisition Skeleton (Phase 1 & Phase 5)
Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
Target: Raspberry Pi 5

Description:
    Detects and connects to the Arduino Uno over USB serial.
    Reads, parses, and timestamps incoming telemetry data.
    Gracefully handles disconnection, reconnections, and data logging to CSV.

Usage:
    python3 raspberry_pi/acquisition/serial_receiver.py --help
    python3 raspberry_pi/acquisition/serial_receiver.py --duration 30 --output datasets/raw/servo_test_01.csv
"""

import sys
import time
import argparse
import datetime
from pathlib import Path
from typing import Optional, List

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("[ERROR] pyserial is not installed.")
    print("Please run: pip install pyserial (or see requirements.txt)")
    sys.exit(1)


def find_arduino_port() -> Optional[str]:
    """
    Scans available USB serial devices to locate an Arduino Uno or generic CDC ACM/FTDI device.
    Returns the port device string (e.g., '/dev/ttyACM0') or None if not detected.
    """
    ports = serial.tools.list_ports.comports()
    if not ports:
        return None

    # Priority 1: Check known Arduino descriptions and vendor IDs
    for port in ports:
        desc = (port.description or "").lower()
        mfg = (port.manufacturer or "").lower()
        if "arduino" in desc or "arduino" in mfg or "ch340" in desc or "cp210" in desc:
            return port.device

    # Priority 2: Return first standard Linux USB ACM or USB serial device
    for port in ports:
        if port.device.startswith(("/dev/ttyACM", "/dev/ttyUSB")):
            return port.device

    # Fallback to the first available port
    return ports[0].device


class SerialReceiver:
    """Manages the serial connection and data reception from Arduino Uno."""

    def __init__(self, port: Optional[str] = None, baud_rate: int = 115200, timeout: float = 2.0):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None
        self.total_records = 0

    def connect(self) -> bool:
        """Establishes or re-establishes serial communication with Arduino."""
        if not self.port:
            detected = find_arduino_port()
            if not detected:
                print("[WAIT] No serial port detected. Please plug in Arduino Uno via USB...")
                return False
            self.port = detected

        try:
            print(f"[CONNECT] Attempting connection to {self.port} at {self.baud_rate} baud...")
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            # Arduino resets on DTR toggle upon opening serial; allow 2 seconds for bootloader
            time.sleep(2.0)
            self.ser.reset_input_buffer()
            print(f"[SUCCESS] Connected to {self.port} successfully.")
            return True
        except (serial.SerialException, OSError) as e:
            print(f"[ERROR] Could not open port {self.port}: {e}")
            self.ser = None
            return False

    def close(self):
        """Safely closes the serial connection."""
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass
        self.ser = None

    def read_record(self) -> Optional[dict]:
        """
        Reads one valid line of telemetry from Arduino.
        Returns a dictionary with parsed fields and host timestamp, or None if invalid/comment.
        """
        if not self.ser or not self.ser.is_open:
            return None

        try:
            raw_bytes = self.ser.readline()
            if not raw_bytes:
                return None  # Read timed out

            line = raw_bytes.decode("utf-8", errors="replace").strip()
            if not line:
                return None

            # Handle comment / diagnostic lines starting with '#'
            if line.startswith("#"):
                print(f"[ARDUINO MSG] {line}")
                return None

            # Split CSV fields
            parts = [p.strip() for p in line.split(",")]
            host_timestamp = datetime.datetime.now().isoformat()

            # For Phase 2 Servo Test: expects 3 fields (timestamp_ms, commanded_angle, status)
            if len(parts) >= 3:
                try:
                    arduino_ms = int(parts[0])
                    angle = int(parts[1])
                    status = parts[2]
                except ValueError:
                    # Ignore partial or garbled lines
                    return None

                self.total_records += 1
                return {
                    "host_timestamp": host_timestamp,
                    "arduino_ms": arduino_ms,
                    "commanded_angle": angle,
                    "status": status,
                    "raw_line": line
                }
            else:
                # Raw unparsed line with fewer than 3 fields
                return {
                    "host_timestamp": host_timestamp,
                    "raw_line": line
                }

        except (serial.SerialException, OSError) as err:
            print(f"[WARN] Serial read error ({err}). Connection lost?")
            self.close()
            return None


def run_acquisition(args):
    """Main loop for running data acquisition."""
    receiver = SerialReceiver(port=args.port, baud_rate=args.baud, timeout=1.0)

    # Prepare output file if specified
    csv_file = None
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        csv_file = open(out_path, "w", buffering=1, encoding="utf-8")
        # Write CSV header for Phase 2
        csv_file.write("host_timestamp,arduino_ms,commanded_angle,status\n")
        print(f"[STORAGE] Logging data to: {out_path.resolve()}")

    start_time = time.time()
    print("[INFO] Starting Serial Receiver Loop. Press Ctrl+C to terminate.")

    try:
        while True:
            # Check duration limit
            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                print(f"\n[DONE] Specified duration of {args.duration}s reached.")
                break

            # Ensure connection
            if not receiver.ser or not receiver.ser.is_open:
                if not receiver.connect():
                    time.sleep(2.0)
                    continue

            record = receiver.read_record()
            if record:
                if "commanded_angle" in record:
                    # Display live status line
                    print(f"\r[DATA] Host: {record['host_timestamp'][11:19]} | "
                          f"Arduino: {record['arduino_ms']:>6}ms | "
                          f"Angle: {record['commanded_angle']:>3}° | "
                          f"Status: {record['status']:<10} | "
                          f"Total: {receiver.total_records}", end="", flush=True)

                    if csv_file:
                        csv_file.write(f"{record['host_timestamp']},{record['arduino_ms']},"
                                       f"{record['commanded_angle']},{record['status']}\n")
                else:
                    print(f"\n[RAW] {record.get('raw_line')}")

    except KeyboardInterrupt:
        print("\n\n[USER] Stopped by user (Ctrl+C).")
    finally:
        receiver.close()
        if csv_file:
            csv_file.close()
            print(f"[STORAGE] Closed output file. Total records written: {receiver.total_records}")
        print("[EXIT] Serial acquisition shut down cleanly.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Raspberry Pi 5 Serial Receiver for Arduino Uno")
    parser.add_argument("--port", type=str, default=None, help="Serial port path (e.g. /dev/ttyACM0). Auto-detects if omitted.")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("--output", type=str, default=None, help="Path to save output CSV file")
    parser.add_argument("--duration", type=int, default=0, help="Duration in seconds (0 = run indefinitely until Ctrl+C)")

    parsed_args = parser.parse_args()
    run_acquisition(parsed_args)
