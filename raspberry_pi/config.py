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
