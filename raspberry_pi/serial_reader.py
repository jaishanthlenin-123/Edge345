#!/usr/bin/env python3
"""
Robust USB Serial Communication Engine
Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
Target: Raspberry Pi 5

Features:
    - Auto-detects Arduino Uno on /dev/ttyUSB* or /dev/ttyACM*
    - Automatic reconnection handling with recovery
    - Multi-format parser:
        1. 10-field standardized CSV telemetry
        2. 8-field compact CSV telemetry
        3. 12-field legacy CSV telemetry
        4. Multi-line diagnostic test block telemetry
    - Tracks packet loss and sequence continuity
"""

import sys
import time
import re
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Generator

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    raise ImportError("pyserial is required. Install via: pip install pyserial")

from raspberry_pi.config import (
    SERIAL_BAUD_RATE,
    SERIAL_TIMEOUT_S,
    TELEMETRY_COLUMNS,
    PREFERRED_PORTS,
    VOLTAGE_DIVIDER_RATIO,
    ACS712_SENSITIVITY_V_PER_A,
    ACS712_NOMINAL_ZERO_V
)


def find_serial_port() -> Optional[str]:
    """Finds the connected Arduino Uno USB serial port."""
    ports = serial.tools.list_ports.comports()
    if not ports:
        return None

    # Priority 1: Check known Arduino descriptions and hardware IDs
    for p in ports:
        desc = (p.description or "").lower()
        mfg = (p.manufacturer or "").lower()
        hwid = (p.hwid or "").lower()
        if any(k in desc or k in mfg or k in hwid for k in ("arduino", "ch340", "cp210", "1a86:7523", "ftdi")):
            return p.device

    # Priority 2: Preferred device paths
    for pref in PREFERRED_PORTS:
        if Path(pref).exists():
            return pref

    # Priority 3: Strictly USB/ACM devices (exclude onboard AMA UARTs)
    for p in ports:
        if p.device.startswith(("/dev/ttyUSB", "/dev/ttyACM")):
            return p.device

    return None


class SerialReader:
    """Manages serial connection, packet parsing, and stream continuity."""

    def __init__(self, port: Optional[str] = None, baud_rate: int = SERIAL_BAUD_RATE):
        self.port = port
        self.baud_rate = baud_rate
        self.ser: Optional[serial.Serial] = None
        self.is_connected = False
        self.total_packets_received = 0
        self.total_packets_dropped = 0
        self.last_sequence = -1

        # State machine for multiline diagnostic block parsing
        self._block_state = {}
        self._block_section = ""

    def connect(self) -> bool:
        """Connects or reconnects to the Arduino serial port."""
        if not self.port or not Path(self.port).exists():
            detected = find_serial_port()
            if not detected:
                return False
            self.port = detected

        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=SERIAL_TIMEOUT_S)
            time.sleep(1.8)  # Allow bootloader DTR auto-reset settling
            self.ser.reset_input_buffer()
            self.is_connected = True
            return True
        except (serial.SerialException, OSError):
            self.close()
            return False

    def close(self):
        """Safely closes the serial port."""
        self.is_connected = False
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass
        self.ser = None

    def parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parses incoming serial lines across CSV and multiline diagnostic formats."""
        line = line.strip()
        if not line:
            return None

        host_ts = datetime.datetime.now().isoformat()

        # -------------------------------------------------------------
        # 1. Check for CSV formats (comma-separated lines)
        # -------------------------------------------------------------
        if "," in line and not line.startswith("#") and "timestamp_ms" not in line:
            parts = [p.strip() for p in line.split(",")]

            # Format A: 10-column standardized format
            if len(parts) == 10:
                try:
                    record = {
                        "host_timestamp": host_ts,
                        "timestamp_ms": int(parts[0]),
                        "sequence": int(parts[1]),
                        "servo_angle": int(parts[2]),
                        "voltage_v": float(parts[3]),
                        "current_a": float(parts[4]),
                        "accel_x": int(parts[5]),
                        "accel_y": int(parts[6]),
                        "accel_z": int(parts[7]),
                        "sound_rms": float(parts[8]),
                        "sound_p2p": int(parts[9]),
                        "format": "standard_10col"
                    }
                    self.total_packets_received += 1
                    self.last_sequence = record["sequence"]
                    return record
                except ValueError:
                    self.total_packets_dropped += 1
                    return None

            # Format B: 8-column compact format
            elif len(parts) == 8:
                try:
                    self.total_packets_received += 1
                    return {
                        "host_timestamp": host_ts,
                        "timestamp_ms": int(parts[0]),
                        "sequence": self.total_packets_received,
                        "servo_angle": int(parts[1]),
                        "voltage_v": float(parts[2]),
                        "current_a": float(parts[3]),
                        "accel_x": int(parts[4]),
                        "accel_y": int(parts[5]),
                        "accel_z": int(parts[6]),
                        "sound_rms": float(parts[7]),
                        "sound_p2p": int(parts[7]),
                        "format": "standard_8col"
                    }
                except ValueError:
                    self.total_packets_dropped += 1
                    return None

            # Format C: 12-column legacy format
            elif len(parts) >= 12:
                try:
                    acs_v = float(parts[7])
                    v_out = float(parts[9])
                    curr = round((acs_v - ACS712_NOMINAL_ZERO_V) / ACS712_SENSITIVITY_V_PER_A, 3)
                    if abs(curr) < 0.015:
                        curr = 0.0
                    volt = round(v_out * VOLTAGE_DIVIDER_RATIO, 2)

                    self.total_packets_received += 1
                    return {
                        "host_timestamp": host_ts,
                        "timestamp_ms": int(parts[0]),
                        "sequence": int(parts[1]),
                        "servo_angle": int(parts[2]),
                        "voltage_v": volt,
                        "current_a": curr,
                        "accel_x": int(parts[3]),
                        "accel_y": int(parts[4]),
                        "accel_z": int(parts[5]),
                        "sound_rms": float(parts[10]),
                        "sound_p2p": int(parts[11]),
                        "format": "legacy_12col_mapped"
                    }
                except ValueError:
                    self.total_packets_dropped += 1
                    return None

            else:
                self.total_packets_dropped += 1
                return None

        # Corrupted / noisy line containing non-ASCII / control bytes
        if any(ord(c) < 32 and c not in "\r\n\t" for c in line) or any(ord(c) > 126 for c in line):
            self.total_packets_dropped += 1
            return None

        # -------------------------------------------------------------
        # 2. Check for Multiline Hardware Diagnostic Block format
        # -------------------------------------------------------------
        if "[1] SERVO" in line:
            self._block_section = "SERVO"
        elif "[2] ACCEL" in line:
            self._block_section = "ACCEL"
        elif "[3] ACS" in line:
            self._block_section = "ACS"
        elif "[4] VOLT" in line:
            self._block_section = "VOLT"
        elif "[5] MAX" in line:
            self._block_section = "MIC"
        elif "TIME:" in line:
            m = re.search(r"TIME:\s*([\d\.]+)", line)
            if m:
                self._block_state["timestamp_ms"] = int(float(m.group(1)) * 1000)

        if self._block_section == "SERVO" and "Current Position" in line:
            m = re.search(r"(\d+)\s*degrees", line)
            if m:
                self._block_state["servo_angle"] = int(m.group(1))
        elif self._block_section == "ACCEL":
            m = re.search(r"(X|Y|Z)\s*Axis\s*:\s*(\d+)", line)
            if m:
                axis = m.group(1).lower()
                self._block_state[f"accel_{axis}"] = int(m.group(2))
        elif self._block_section == "ACS" and "Output Voltage" in line:
            m = re.search(r"([\d\.]+)\s*V", line)
            if m:
                v = float(m.group(1))
                # Dynamic zero offset check (nominal ~0.90V on test board or 2.50V on 5V supply)
                zero_ref = 0.90 if v < 1.5 else 2.50
                self._block_state["current_a"] = round(abs(v - zero_ref) / 0.185, 3)
        elif self._block_section == "VOLT" and "Output Voltage" in line:
            m = re.search(r"([\d\.]+)\s*V", line)
            if m:
                self._block_state["voltage_v"] = round(float(m.group(1)) * 5.0, 2)
        elif self._block_section == "MIC":
            m_rms = re.search(r"Audio RMS\s*:\s*([\d\.]+)", line)
            if m_rms:
                self._block_state["sound_rms"] = float(m_rms.group(1))
            m_p2p = re.search(r"Peak-to-Peak\s*:\s*(\d+)", line)
            if m_p2p:
                self._block_state["sound_p2p"] = int(m_p2p.group(1))

        # Check for block completion
        if "STATUS: SENSOR READINGS UPDATED" in line:
            if "servo_angle" in self._block_state and "accel_x" in self._block_state:
                self.total_packets_received += 1
                record = {
                    "host_timestamp": host_ts,
                    "timestamp_ms": self._block_state.get("timestamp_ms", int(time.time() * 1000)),
                    "sequence": self.total_packets_received,
                    "servo_angle": self._block_state.get("servo_angle", 90),
                    "voltage_v": self._block_state.get("voltage_v", 0.0),
                    "current_a": self._block_state.get("current_a", 0.0),
                    "accel_x": self._block_state.get("accel_x", 350),
                    "accel_y": self._block_state.get("accel_y", 350),
                    "accel_z": self._block_state.get("accel_z", 350),
                    "sound_rms": self._block_state.get("sound_rms", 0.0),
                    "sound_p2p": self._block_state.get("sound_p2p", 0),
                    "format": "diagnostic_block_mapped"
                }
                self._block_state.clear()
                return record

        return None

    def read_stream(self) -> Generator[Dict[str, Any], None, None]:
        """Yields validated records continuously, handling disconnects automatically."""
        while True:
            if not self.is_connected or not self.ser or not self.ser.is_open:
                if not self.connect():
                    time.sleep(1.0)
                    continue

            try:
                raw_bytes = self.ser.readline()
                if not raw_bytes:
                    continue

                line_str = raw_bytes.decode("utf-8", errors="replace")
                record = self.parse_line(line_str)
                if record:
                    yield record

            except (serial.SerialException, OSError):
                self.close()
                time.sleep(1.0)
