"""
Configuration Settings for Servo Motor Condition Monitoring System
Target: Raspberry Pi 5
"""

from pathlib import Path

# Base project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "datasets"
RAW_DATA_DIR = DATASETS_DIR / "raw"
NORMAL_DATA_DIR = DATASETS_DIR / "normal"
TEST_DATA_DIR = DATASETS_DIR / "test"
PROCESSED_DATA_DIR = DATASETS_DIR / "processed"
SAVED_MODELS_DIR = BASE_DIR / "saved_models"
REPORTS_DIR = BASE_DIR / "reports"
DATABASE_DIR = BASE_DIR / "database"

# Ensure all runtime directories exist
for directory in (RAW_DATA_DIR, NORMAL_DATA_DIR, TEST_DATA_DIR, PROCESSED_DATA_DIR, SAVED_MODELS_DIR, REPORTS_DIR, DATABASE_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# SQLite Database path
DATABASE_PATH = DATABASE_DIR / "telemetry_history.db"

# Serial communication
SERIAL_BAUD_RATE = 115200
SERIAL_TIMEOUT_S = 1.0
PREFERRED_PORTS = ("/dev/ttyUSB0", "/dev/ttyACM0")

# Telemetry Schema (10-field standardized specification)
TELEMETRY_COLUMNS = [
    "timestamp_ms",
    "sequence",
    "servo_angle",
    "voltage_v",
    "current_a",
    "accel_x",
    "accel_y",
    "accel_z",
    "sound_rms",
    "sound_p2p"
]

# Physical calibration constants
ADC_REF_V = 5.0
VOLTAGE_DIVIDER_RATIO = 5.0
ACS712_SENSITIVITY_V_PER_A = 0.185  # 5A module: 185 mV/A (20A = 0.100, 30A = 0.066)
ACS712_NOMINAL_ZERO_V = 2.50

# Normal operational boundaries for live health checks & statistical thresholding
NORMAL_LIMITS = {
    "voltage_min_v": 4.50,
    "voltage_max_v": 5.50,
    "current_max_a": 0.200,   # User threshold: trigger anomaly when current exceeds 0.200A (200mA)
    "accel_min": 100,
    "accel_max": 900,
    "sound_p2p_max": 600,
    "sound_rms_max": 150.0
}

# ==============================================================================
# SECURE MQTT (MQTTS) CONFIGURATION
# ==============================================================================
import os

MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT_TLS = int(os.getenv("MQTT_BROKER_PORT_TLS", "8883"))
MQTT_BROKER_PORT_PLAIN = int(os.getenv("MQTT_BROKER_PORT_PLAIN", "1883"))
MQTT_USE_TLS = os.getenv("MQTT_USE_TLS", "true").lower() in ("true", "1", "yes")

# Authentication via Environment Variables (Never commit credentials)
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "edge_servo_operator")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")  # Supplied via environment or secret manager

# TLS / X.509 Certificates (Paths on Raspberry Pi)
CERT_DIR = BASE_DIR / "certs"
MQTT_CA_CERT = os.getenv("MQTT_CA_CERT", str(CERT_DIR / "ca.crt"))
MQTT_CLIENT_CERT = os.getenv("MQTT_CLIENT_CERT", str(CERT_DIR / "client.crt"))
MQTT_CLIENT_KEY = os.getenv("MQTT_CLIENT_KEY", str(CERT_DIR / "client.key"))
MQTT_TLS_INSECURE = os.getenv("MQTT_TLS_INSECURE", "false").lower() in ("true", "1")

# Client behavior
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "rpi5-servo-edge-node01")
MQTT_KEEPALIVE_S = 60
MQTT_DEFAULT_QOS = 1
MQTT_TOPIC_PREFIX = "motor/servo01"

# Hierarchical M4 Topic Schema
MQTT_TOPICS = {
    "imu": f"{MQTT_TOPIC_PREFIX}/sensors/imu",
    "current": f"{MQTT_TOPIC_PREFIX}/sensors/current",
    "voltage": f"{MQTT_TOPIC_PREFIX}/sensors/voltage",
    "audio": f"{MQTT_TOPIC_PREFIX}/sensors/audio",
    "status": f"{MQTT_TOPIC_PREFIX}/status",
    "alerts": f"{MQTT_TOPIC_PREFIX}/alerts",
    "health": f"{MQTT_TOPIC_PREFIX}/health"
}

# ==============================================================================
# INDUSTRIAL PLC (MODBUS TCP) CONFIGURATION
# ==============================================================================
PLC_MODBUS_HOST = os.getenv("PLC_MODBUS_HOST", "0.0.0.0")
PLC_MODBUS_PORT = int(os.getenv("PLC_MODBUS_PORT", "5020"))  # Port 5020 for unprivileged; 502 for standard
PLC_SLAVE_ID = int(os.getenv("PLC_SLAVE_ID", "1"))

# Standard Industrial 16-bit Modbus Register Allocation
MODBUS_REGISTER_MAP = {
    # Input Registers (30001+, Function Code 04: Read-Only Sensor Telemetry)
    "INPUT_REGISTERS": {
        "SERVO_ANGLE_DEG": 0,       # 30001: 0-180 degrees
        "VOLTAGE_MV": 1,            # 30002: Scaled mV (e.g. 5000 = 5.00V)
        "CURRENT_MA": 2,            # 30003: Scaled mA (e.g. 92 = 0.092A)
        "ACCEL_X_RAW": 3,           # 30004: Raw ADC (0-1023)
        "ACCEL_Y_RAW": 4,           # 30005: Raw ADC (0-1023)
        "ACCEL_Z_RAW": 5,           # 30006: Raw ADC (0-1023)
        "SOUND_RMS_X10": 6,         # 30007: Sound RMS scaled x10
        "SOUND_P2P_RAW": 7,         # 30008: Audio peak-to-peak (0-1023)
        "ANOMALY_SCORE_X1000": 8,   # 30009: Anomaly score scaled (0-1000)
        "PACKETS_TOTAL": 9,         # 30010: Total packets received counter
    },
    # Holding Registers (40001+, Function Code 03/06/16: Read/Write Control & Config)
    "HOLDING_REGISTERS": {
        "ANOMALY_THRESHOLD_X100": 0, # 40001: Scaled threshold (default 65 = 0.65)
        "CURRENT_LIMIT_MA": 1,       # 40002: Safety limit in mA (default 200 = 0.200A)
        "SAMPLING_RATE_MS": 2,       # 40003: Rate in ms (default 100ms)
        "COMMANDED_ANGLE_DEG": 3,    # 40004: Commanded servo target angle (0-180)
    },
    # Discrete Inputs (10001+, Function Code 02: Read-Only Binary Status)
    "DISCRETE_INPUTS": {
        "SYSTEM_HEALTHY": 0,        # 10001: 1=Normal, 0=Degraded/Fault
        "ARDUINO_CONNECTED": 1,     # 10002: 1=Connected, 0=Disconnected
        "ANOMALY_ACTIVE": 2,        # 10003: 1=Anomaly Flagged, 0=Normal
        "RECORDING_ACTIVE": 3,      # 10004: 1=Recording, 0=Idle
    },
    # Coils (00001+, Function Code 01/05/15: Read/Write Digital Actuation & Reset)
    "COILS": {
        "EMERGENCY_STOP": 0,        # 00001: 1=Trigger E-Stop, 0=Normal
        "ACKNOWLEDGE_ALARM": 1,     # 00002: 1=Reset/Acknowledge alert
        "START_RECORDING": 2,       # 00003: 1=Start session
        "RESET_STATISTICS": 3,      # 00004: 1=Clear packet counters
    }
}

