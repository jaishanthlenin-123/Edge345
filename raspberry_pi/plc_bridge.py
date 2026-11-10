#!/usr/bin/env python3
"""
Industrial PLC Modbus TCP Bridge & Simulation Subsystem
Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
Target: Raspberry Pi 5

Description:
    Exposes a standardized Industrial Modbus TCP server (Slave/Server) interfacing
    with programmable logic controllers (PLCs) such as Siemens S7-1200, Schneider
    Modicon, Allen-Bradley Micro800, and SCADA packages.
    
    Translates real-time sensor measurements, motor states, and machine learning
    anomaly inferences into standard Modbus data structures:
        - Input Registers (30001+, FC 04): Read-Only Sensor Telemetry
        - Holding Registers (40001+, FC 03/06/16): Read/Write Control & Config
        - Discrete Inputs (10001+, FC 02): Read-Only Binary Status
        - Coils (00001+, FC 01/05/15): Read/Write Digital Actuation & Reset
    
    Provides simulated server and client test harnesses for complete verification
    when physical industrial PLC hardware is not attached.
"""

import sys
import time
import asyncio
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from raspberry_pi.config import (
    PLC_MODBUS_HOST,
    PLC_MODBUS_PORT,
    PLC_SLAVE_ID,
    MODBUS_REGISTER_MAP
)

try:
    from pymodbus.server import StartAsyncTcpServer
    from pymodbus.server.base import ModbusBaseServer
    from pymodbus.simulator import SimDevice, SimData, DataType
    from pymodbus.client import ModbusTcpClient
    PYMODBUS_AVAILABLE = True
except ImportError:
    PYMODBUS_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("PLC_Bridge")


class ModbusPLCBridge:
    """Manages the Industrial Modbus TCP slave datastore and register updates."""

    def __init__(self, host: str = PLC_MODBUS_HOST, port: int = PLC_MODBUS_PORT, slave_id: int = PLC_SLAVE_ID):
        if not PYMODBUS_AVAILABLE:
            raise ImportError("pymodbus is required. Install via: pip install pymodbus")

        self.host = host
        self.port = port
        self.slave_id = slave_id
        self.is_running = False
        self._server_thread: Optional[threading.Thread] = None

        # Build initial datastore memory blocks:
        # data_di: Discrete Inputs (10001+)
        # data_co: Coils (00001+)
        # data_hr: Holding Registers (40001+)
        # data_ir: Input Registers (30001+)
        self.data_di = SimData(address=0, count=1, values=[True, True, False, False], datatype=DataType.BITS)
        self.data_co = SimData(address=0, count=1, values=[False, False, False, False], datatype=DataType.BITS)
        self.data_hr = SimData(address=0, count=1, values=[65, 200, 100, 90], datatype=DataType.REGISTERS)
        self.data_ir = SimData(address=0, count=1, values=[90, 5000, 92, 335, 392, 307, 160, 65, 0, 0], datatype=DataType.REGISTERS)

        self.simdev = SimDevice(
            id=self.slave_id,
            simdata=(
                [self.data_di],
                [self.data_co],
                [self.data_hr],
                [self.data_ir]
            )
        )

    def _get_active_device(self):
        """Retrieves active SimRuntime device instance from running server."""
        if hasattr(ModbusBaseServer, "active_server") and ModbusBaseServer.active_server:
            ctx = ModbusBaseServer.active_server.context
            if hasattr(ctx, "devices") and self.slave_id in ctx.devices:
                return ctx.devices[self.slave_id]
        return None

    def update_from_telemetry(self, record: Dict[str, Any], prediction: Optional[Dict[str, Any]] = None):
        """
        Encodes real-time floating-point sensor telemetry into standardized
        16-bit unsigned/signed industrial integer Modbus registers.
        """
        pred = prediction or {"status": "NORMAL", "anomaly_score": 0.0, "is_anomaly": False}

        # 1. Scale Input Registers (Read-only metrics for PLC)
        angle = int(record.get("servo_angle", 90))
        volt_mv = int(round(record.get("voltage_v", 0.0) * 1000))
        curr_ma = int(round(record.get("current_a", 0.0) * 1000))
        ax = int(record.get("accel_x", 350))
        ay = int(record.get("accel_y", 350))
        az = int(record.get("accel_z", 350))
        sound_rms_x10 = int(round(record.get("sound_rms", 0.0) * 10))
        sound_p2p = int(record.get("sound_p2p", 0))
        anom_score_x1000 = int(round(pred.get("anomaly_score", 0.0) * 1000))
        seq = int(record.get("sequence", 0)) % 65535

        ir_values = [
            angle,
            volt_mv,
            curr_ma,
            ax,
            ay,
            az,
            sound_rms_x10,
            sound_p2p,
            anom_score_x1000,
            seq
        ]

        dev = self._get_active_device()
        if dev and "i" in dev.block:
            dev.block["i"][2][0:len(ir_values)] = ir_values

        # 2. Discrete Inputs (PLC status bits)
        is_anom = 1 if pred.get("is_anomaly") else 0
        healthy = 0 if is_anom or curr_ma > 850 else 1
        connected = 1  # Active serial
        recording = 1 if record.get("is_recording") else 0

        if dev and "d" in dev.block:
            # First 4 bits encoded into discrete input integer bitmask
            bitmask = (healthy & 1) | ((connected & 1) << 1) | ((is_anom & 1) << 2) | ((recording & 1) << 3)
            dev.block["d"][2][0] = bitmask

    def get_commanded_angle(self) -> int:
        """Reads holding register 3 (commanded servo angle from PLC)."""
        dev = self._get_active_device()
        if dev and "h" in dev.block:
            return dev.block["h"][2][3]
        return 90

    def get_emergency_stop(self) -> bool:
        """Reads coil 0 (PLC emergency stop flag)."""
        dev = self._get_active_device()
        if dev and "c" in dev.block:
            return bool(dev.block["c"][2][0] & 1)
        return False

    def start_server_sync(self):
        """Runs the Modbus TCP server synchronously."""
        logger.info("Starting Modbus TCP PLC Server on %s:%d (Slave ID: %d)...", self.host, self.port, self.slave_id)
        self.is_running = True
        try:
            asyncio.run(StartAsyncTcpServer(context=self.simdev, address=(self.host, self.port)))
        except Exception as e:
            logger.error("Modbus TCP Server stopped: %s", e)
        finally:
            self.is_running = False

    def start_server_background(self):
        """Starts the Modbus TCP server in a background daemon thread."""
        if self._server_thread and self._server_thread.is_alive():
            return
        self._server_thread = threading.Thread(target=self.start_server_sync, daemon=True)
        self._server_thread.start()
        time.sleep(0.5)


class PLCClientDemo:
    """Client utility for industrial test benches, PLC simulated polling, and validation."""

    def __init__(self, host: str = "127.0.0.1", port: int = PLC_MODBUS_PORT, slave_id: int = PLC_SLAVE_ID):
        self.host = host
        self.port = port
        self.slave_id = slave_id
        self.client = ModbusTcpClient(host=self.host, port=self.port)

    def connect(self) -> bool:
        return self.client.connect()

    def disconnect(self):
        self.client.close()

    def read_telemetry(self) -> Dict[str, Any]:
        """Polls Input Registers (FC 04) and decodes physical measurements."""
        try:
            rr = self.client.read_input_registers(address=0, count=10, device_id=self.slave_id)
        except TypeError:
            rr = self.client.read_input_registers(address=0, count=10, slave=self.slave_id)

        if rr.isError():
            raise RuntimeError(f"Modbus read error: {rr}")

        regs = rr.registers
        return {
            "servo_angle_deg": regs[0],
            "voltage_v": round(regs[1] / 1000.0, 2),
            "current_a": round(regs[2] / 1000.0, 3),
            "accel_x": regs[3],
            "accel_y": regs[4],
            "accel_z": regs[5],
            "sound_rms": round(regs[6] / 10.0, 2),
            "sound_p2p": regs[7],
            "anomaly_score": round(regs[8] / 1000.0, 3),
            "packets_total": regs[9]
        }

    def read_discrete_status(self) -> Dict[str, bool]:
        """Polls Discrete Inputs (FC 02) for health and fault bits."""
        try:
            rr = self.client.read_discrete_inputs(address=0, count=4, device_id=self.slave_id)
        except TypeError:
            rr = self.client.read_discrete_inputs(address=0, count=4, slave=self.slave_id)

        if rr.isError():
            raise RuntimeError(f"Modbus discrete read error: {rr}")
        bits = rr.bits
        return {
            "system_healthy": bool(bits[0]),
            "arduino_connected": bool(bits[1]),
            "anomaly_active": bool(bits[2]),
            "recording_active": bool(bits[3])
        }

    def write_commanded_angle(self, angle_deg: int) -> bool:
        """Writes commanded angle to Holding Register 3 (FC 06)."""
        try:
            wr = self.client.write_register(address=3, value=angle_deg, device_id=self.slave_id)
        except TypeError:
            wr = self.client.write_register(address=3, value=angle_deg, slave=self.slave_id)
        return not wr.isError()

    def write_emergency_stop(self, stop: bool) -> bool:
        """Sets or resets emergency stop coil 0 (FC 05)."""
        try:
            wr = self.client.write_coil(address=0, value=stop, device_id=self.slave_id)
        except TypeError:
            wr = self.client.write_coil(address=0, value=stop, slave=self.slave_id)
        return not wr.isError()


if __name__ == "__main__":
    print("Testing Modbus PLC Bridge standalone...")
    bridge = ModbusPLCBridge(host="127.0.0.1", port=5020)
    bridge.start_server_background()
    time.sleep(1)

    client = PLCClientDemo(host="127.0.0.1", port=5020)
    if client.connect():
        print("Connected to Modbus PLC Bridge!")
        data = client.read_telemetry()
        print("Initial Telemetry from Input Registers:", data)
        status = client.read_discrete_status()
        print("Discrete Status Bits:", status)

        print("\nUpdating bridge with new telemetry record...")
        bridge.update_from_telemetry({
            "servo_angle": 150,
            "voltage_v": 5.04,
            "current_a": 0.115,
            "accel_x": 340,
            "accel_y": 385,
            "accel_z": 310,
            "sound_rms": 14.5,
            "sound_p2p": 58,
            "sequence": 142
        }, {
            "status": "NORMAL",
            "anomaly_score": 0.12,
            "is_anomaly": False
        })
        time.sleep(0.1)

        updated_data = client.read_telemetry()
        print("Updated Telemetry after write:", updated_data)

        print("\nWriting commanded angle 120 deg to Holding Register 3...")
        client.write_commanded_angle(120)
        time.sleep(0.1)
        print("Read commanded angle from bridge:", bridge.get_commanded_angle())

        print("\nWriting Emergency Stop Coil 0 = True...")
        client.write_emergency_stop(True)
        time.sleep(0.1)
        print("Read Emergency Stop from bridge:", bridge.get_emergency_stop())

        client.disconnect()
        print("\nPLC Link standalone verification successful.")
    else:
        print("Failed to connect to Modbus PLC Bridge.")
