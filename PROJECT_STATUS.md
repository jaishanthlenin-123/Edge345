# Project Status: SG90 Servo Motor Condition Monitoring and Anomaly Detection System

**Last Updated:** November 6, 2026  
**System Architecture:** Arduino Uno R3 (Acquisition & Actuation) + Raspberry Pi 5 (Edge ML, Database, REST API, Live Dashboard)  
**Hardware Pin Plan:** Servo PWM: `D9` | ACS712: `A0` | Voltage Sensor: `A1` | MAX9814: `A2` | Accelerometer X, Y, Z: `A3, A4, A5`

---

## 1. Development Phases Tracking Matrix

| Phase | Description | Status | Implementation & Validation Evidence |
|:---:|---|:---:|---|
| **Phase 1** | **Code & Hardware Audit** | 🟢 VERIFIED | Audited `arduino/servo_test/servo_test.ino`; backup created at `servo_test.ino.bak`. Full audit report archived in `documentation/phase1_code_audit.md`. |
| **Phase 2** | **Arduino Firmware Development** | 🟢 IMPLEMENTED | Modular firmware written in `arduino/servo_monitor/` (`servo_monitor.ino`, `calibration.h`, `config.h`) and `arduino/servo_test/servo_test.ino`. Non-blocking `millis()` timing, auto-calibrated zero-current baseline, rapid 3.5ms acoustic burst, and 10-field standardized CSV telemetry at 115200 baud. |
| **Phase 3** | **Raspberry Pi Serial Integration** | 🟢 TESTED | `raspberry_pi/serial_reader.py` auto-discovers `/dev/ttyUSB*` / `/dev/ttyACM*`, handles automatic reconnects, validates packets, and supports both standard 10-field and legacy formats. |
| **Phase 4** | **Data Logging & SQLite Database** | 🟢 TESTED | `raspberry_pi/database.py` manages tables for sessions, high-resolution telemetry, and alerts. `raspberry_pi/data_logger.py` buffers and persists to CSV and SQLite. Tested successfully. |
| **Phase 5** | **Sensor Calibration Subsystem** | 🟢 TESTED | `raspberry_pi/sensor_calibration.py` computes statistical baselines, zero-current voltage, divider scaling, and sensor health checks. |
| **Phase 6** | **Experimental Data Collection** | 🟢 TESTED | `scripts/collect_dataset.sh` and `raspberry_pi/data_logger.py` support `normal`, `test`, and `anomaly` recording sessions with live terminal feedback. Real baseline dataset logged to `datasets/raw/`. |
| **Phase 7** | **Signal Processing & Feature Extraction** | 🟢 TESTED | `raspberry_pi/feature_extraction.py` extracts 21 statistical, vibration (RMS, P2P, Crest Factor), acoustic (RMS, energy), electrical, and motion dynamics features over sliding windows. |
| **Phase 8** | **Machine Learning Anomaly Detection** | 🟢 TESTED | `raspberry_pi/models/anomaly_detector.py` implements multivariate unsupervised anomaly scoring with feature attribution. Trained and verified on recorded data; model and metadata serialized to `saved_models/`. |
| **Phase 9** | **Backend REST API** | 🟢 TESTED | Multi-threaded HTTP server in `raspberry_pi/dashboard/server.py` and FastAPI application in `backend/app/main.py` serving `/api/status`, `/api/sensors/latest`, `/api/sensors/history`, `/api/anomalies`, and session controls. Verified via automated HTTP integration tests. |
| **Phase 10** | **Live Monitoring Dashboard** | 🟢 TESTED | Modern dark industrial single-page application (`index.html`, `app.js`, `style.css`) in `raspberry_pi/dashboard/static/`. Features real-time metric cards, anomaly score gauge, live 60 FPS HTML5 canvas charts, recording controls, and live alert feed. |
| **Phase 11** | **Alerts & Condition Monitoring** | 🟢 TESTED | Hybrid alerting combining hard electrical thresholds (overcurrent > 0.85A, voltage deviation) and machine learning statistical Z-score thresholds. Alerts persisted to SQLite and streamed to dashboard. |
| **Phase 12** | **Deployment & Automation** | 🟢 IMPLEMENTED | Systemd service `scripts/servo-monitoring.service` and runner scripts `scripts/start_dashboard.sh`, `scripts/collect_dataset.sh`, `scripts/train_model.py` created and tested. |

*Status Legend:*  
- ⚪ NOT STARTED  
- 🟡 IN PROGRESS  
- 🔵 IMPLEMENTED (Code complete, awaiting test)  
- 🟢 TESTED (Automated & software verified)  
- 🟢 VERIFIED ON HARDWARE (Physically tested on running hardware)

---

## 2. Hardware Allocation & Active Pin Map

| Component | Physical Pin | Function | Electrical Constraints & Safety |
|---|:---:|---|---|
| **SG90 Servo Signal** | **D9** | Hardware Timer1 PWM (50 Hz) | Commanded angles: 30°, 90°, 150°, 90°. |
| **ACS712 Current Sensor** | **A0** | Motor Current Telemetry | Hall-effect sensor in series with servo +5V line. Auto-zeros quiescent voltage ($V_{zero} \approx 2.5\text{V}$). Configurable sensitivity ($185\text{ mV/A}$ default for 5A). |
| **0–25V Voltage Sensor** | **A1** | Motor Supply Voltage | 5:1 resistive divider ($30\text{k}\Omega / 7.5\text{k}\Omega$). Measures external servo power supply in parallel. |
| **MAX9814 Microphone** | **A2** | Acoustic Gear Noise | Analog audio amplifier OUT pin. 32-sample rapid burst computes RMS and Peak-to-Peak. |
| **Accelerometer X-Axis** | **A3** | Mechanical Vibration X | 3-axis analog accelerometer X_OUT. |
| **Accelerometer Y-Axis** | **A4** | Mechanical Vibration Y | 3-axis analog accelerometer Y_OUT. |
| **Accelerometer Z-Axis** | **A5** | Mechanical Vibration Z | 3-axis analog accelerometer Z_OUT. |
| **Ground Reference** | **GND** | Common 0V Reference | **CRITICAL:** Arduino GND, external 5V supply negative, and all sensor grounds MUST be tied together. |

---

## 3. Project Directory Index

```text
Edge 345/
├── README.md                                  # Master System Documentation & Setup Guide
├── PROJECT_STATUS.md                          # Live Phase Tracking Matrix
├── requirements.txt                           # Python Dependencies
├── run_servo_test.sh                          # Quick terminal telemetry runner
│
├── arduino/
│   ├── servo_monitor/                         # Phase 2: Modular Production Firmware
│   │   ├── servo_monitor.ino                  # Main Arduino sketch
│   │   ├── config.h                           # Pin definitions & sampling timing
│   │   └── calibration.h                      # Sensor scaling & zero-calibration routines
│   ├── servo_test/
│   │   ├── servo_test.ino                     # Standalone test sketch (updated with 10-field CSV)
│   │   └── servo_test.ino.bak                 # Phase 1 original backup
│
├── raspberry_pi/
│   ├── config.py                              # Central hardware & path configuration
│   ├── serial_reader.py                       # USB serial acquisition engine with auto-reconnect
│   ├── database.py                            # SQLite persistence layer (sessions, telemetry, alerts)
│   ├── data_logger.py                         # Dual CSV and SQLite dataset recorder
│   ├── sensor_calibration.py                  # Live electrical verification & health check tool
│   ├── feature_extraction.py                  # 21-dimensional sliding-window feature extractor
│   ├── models/
│   │   └── anomaly_detector.py                # Multivariate Isolation Forest / Statistical detector
│   └── dashboard/
│       ├── server.py                          # Multi-threaded REST & Static Web Server
│       └── static/
│           ├── index.html                     # Dark industrial dashboard UI
│           ├── style.css                      # Modern industrial responsive styling
│           └── app.js                         # 10 Hz real-time chart rendering & state machine
│
├── backend/
│   └── app/
│       └── main.py                            # FastAPI enterprise backend application
│
├── datasets/
│   ├── raw/                                   # Raw CSV streaming records
│   ├── normal/                                # Unloaded baseline training datasets
│   ├── test/                                  # Evaluation datasets
│   └── processed/                             # Feature-extracted datasets
│
├── saved_models/
│   ├── anomaly_model_latest.pkl               # Serialized anomaly model
│   └── anomaly_model_latest.json              # Model hyperparameters & training metadata
│
├── database/
│   └── telemetry_history.db                   # SQLite database (auto-generated)
│
├── documentation/
│   ├── phase1_code_audit.md                   # Phase 1 code audit and findings
│   ├── architecture.md                        # End-to-end communication and data pipeline
│   └── hardware_connections.md                # Wiring schematics and power isolation guide
│
└── scripts/
    ├── start_dashboard.sh                     # Launch live dashboard (Port 8000)
    ├── collect_dataset.sh                     # Start timed dataset recording
    ├── run_calibration.sh                     # Run live sensor calibration analysis
    ├── train_model.py                         # Train ML anomaly detector on CSV datasets
    └── servo-monitoring.service               # Systemd daemon for boot startup
```
