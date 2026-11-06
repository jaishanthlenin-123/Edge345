# SG90 Servo Motor Condition Monitoring and Anomaly Detection System

An autonomous, end-to-end Edge AI Condition Monitoring and Anomaly Detection System deployed on an **Arduino Uno R3** and **Raspberry Pi 5**.

The system monitors mechanical vibration, acoustic noise, electrical current consumption, supply voltage, and rotational dynamics of an SG90 micro-servo motor in real time. It extracts a 21-dimensional multivariate feature space across sliding time windows and executes unsupervised Machine Learning (Isolation Forest / Multivariate Statistical Detection) to identify anomalous operating behavior, mechanical binding, and electrical faults.

---

## 1. System Architecture

```text
               +-------------------------------------------+
               |        SG90 Servo Motor Under Test        |
               +-------------------------------------------+
                     |              |              |
          Acoustic   |    Vibration |      Current | & Voltage
                     v              v              v
               +-----------+  +------------+  +-------------------+
               |  MAX9814  |  |  Analog 3D |  | ACS712 (Series) & |
               | Microphone|  | Accelerom. |  | 0-25V Volt Divider|
               +-----------+  +------------+  +-------------------+
                     |              |              |
                     +-------+      |      +-------+
                             |      |      |
                             v      v      v
                      +--------------------------+
                      |      Arduino Uno R3      |
                      |  - D9: Servo PWM Control |
                      |  - A0-A5: ADC Sampling   |
                      |  - Zero-offset auto-cal  |
                      +--------------------------+
                                   |
                                   | USB Serial (115200 Baud)
                                   v
                      +--------------------------+
                      |      Raspberry Pi 5      |
                      |  - Host Python Engine    |
                      |  - Auto-reconnect Serial |
                      |  - Dual CSV & SQLite DB  |
                      +--------------------------+
                                   |
                     +-------------+-------------+
                     |                           |
                     v                           v
        +-------------------------+  +-------------------------+
        | Feature Extractor (21D) |  |   Dashboard Web Server  |
        | - RMS, Crest Factor     |  | - Port 8000 (Built-in)  |
        | - P2P, Variance, Energy |  | - Real-Time 60 FPS Canvas|
        +-------------------------+  | - Session Recording UI  |
                     |               +-------------------------+
                     v                           |
        +-------------------------+              |
        | Machine Learning Engine |              |
        | - Isolation Forest      |              |
        | - Statistical Z-Scores  |              |
        | - Feature Attribution   |<-------------+
        +-------------------------+
```

---

## 2. Hardware Allocation & Pin Configuration

| Component | Arduino Pin | Module Pin | Description & Electrical Constraints |
|---|:---:|:---:|---|
| **SG90 Servo Signal** | **D9** | Orange/Yellow | PWM position signal (Timer1, 50 Hz). Cycles: `30° -> 90° -> 150° -> 90°`. |
| **ACS712 Current Sensor** | **A0** | OUT | Measures instantaneous motor current. IP+ and IP- wired in **series** with servo +5V line. Zero-current baseline auto-calibrated at boot ($V_{zero} \approx 2.50\text{V}$). |
| **0–25V Voltage Sensor** | **A1** | S | 5:1 resistor divider ($30\text{k}\Omega / 7.5\text{k}\Omega$). Wired in **parallel** across external servo supply terminals. |
| **MAX9814 Microphone** | **A2** | OUT | Analog audio amplifier. Rapid 32-sample burst (~3.5ms) extracts true RMS and Peak-to-Peak acoustic energy. |
| **3-Axis Accelerometer** | **A3** | X_OUT | Analog X-axis acceleration / vibration. |
| **3-Axis Accelerometer** | **A4** | Y_OUT | Analog Y-axis acceleration / vibration. |
| **3-Axis Accelerometer** | **A5** | Z_OUT | Analog Z-axis acceleration / vibration. |
| **Common Ground** | **GND** | GND | **CRITICAL:** Arduino GND, external power supply ground, and all sensor grounds **MUST** be connected together. |

> [!WARNING]
> **ELECTRICAL SAFETY REQUIREMENT:**
> Never power the SG90 servo motor continuously from the Arduino 5V pin! Stalling or sudden movements can pull over **800mA**, triggering USB overcurrent protection or resetting the microcontroller. Power the servo motor from an external regulated 5V power supply, and tie its ground to the Arduino GND.

---

## 3. Standardized Telemetry Protocol

The Arduino firmware transmits a standardized 10-field CSV record every 100ms (10 Hz) at **115200 baud**:

```text
timestamp_ms,sequence,servo_angle,voltage_v,current_a,accel_x,accel_y,accel_z,sound_rms,sound_p2p
```

### Telemetry Field Definitions:
1. `timestamp_ms` (*int*): Milliseconds elapsed since Arduino bootloader startup.
2. `sequence` (*int*): Monotonically increasing record index (monitors dropped packets).
3. `servo_angle` (*int*): Commanded shaft angle in degrees (`30`, `90`, `150`).
4. `voltage_v` (*float*): Calibrated motor supply voltage (Volts).
5. `current_a` (*float*): Calibrated motor current consumption (Amperes).
6. `accel_x` (*int*): Analog accelerometer X-axis raw ADC (0–1023).
7. `accel_y` (*int*): Analog accelerometer Y-axis raw ADC (0–1023).
8. `accel_z` (*int*): Analog accelerometer Z-axis raw ADC (0–1023).
9. `sound_rms` (*float*): Root-Mean-Square acoustic energy (DC bias subtracted).
10. `sound_p2p` (*int*): Peak-to-Peak audio burst amplitude ($\max - \min$).

---

## 4. Quick Start & Execution Guide

### Step 1: Upload Arduino Firmware
1. Open [`arduino/servo_monitor/servo_monitor.ino`](arduino/servo_monitor/servo_monitor.ino) (or [`arduino/servo_test/servo_test.ino`](arduino/servo_test/servo_test.ino)) in the Arduino IDE.
2. Select Board: **Arduino Uno** and your USB Port (`/dev/ttyACM0` or `/dev/ttyUSB0`).
3. Click **Upload**.

### Step 2: Launch the Real-Time Web Dashboard
On your Raspberry Pi 5 terminal:
```bash
./scripts/start_dashboard.sh
```
Open your web browser and navigate to:
```text
http://localhost:8000
```
*(Or `http://<RaspberryPi_IP>:8000` from any computer on the local network).*

You will observe:
- **Live Connection Pill:** Auto-detects and connects to Arduino Uno.
- **Multivariate Anomaly Banner:** Live normal vs. anomaly status with score gauge (0.00 to 1.00) and top contributing sensor drivers.
- **Sensor Cards:** Position (30°-150°), Voltage, Current, Vibration vector, Audio energy.
- **Live 60 FPS Charts:** Real-time waveforms for Current, Voltage, X/Y/Z Acceleration, Audio P2P, and Servo Angle.
- **Dataset Recording UI:** Start and stop named recording sessions into CSV and SQLite.
- **Alert History Log:** Real-time stream of threshold alerts and anomaly events.

---

## 5. Offline CLI Operations

### A. Quick Terminal Telemetry Monitor
To view live incoming telemetry directly in your terminal without opening a browser:
```bash
./run_servo_test.sh
```

### B. Sensor Calibration & Health Check
Verify zero-current baseline, voltage divider scaling, and sensor activity across 30 live samples:
```bash
./scripts/run_calibration.sh
```

### C. Collect a Normal Training Dataset
Collect a dedicated 60-second baseline dataset of unloaded, normal operation:
```bash
./scripts/collect_dataset.sh normal 60
```
Datasets are automatically saved to `datasets/normal/` and indexed in the SQLite database (`database/telemetry_history.db`).

### D. Train the Anomaly Detection Model
Train the multivariate anomaly detection model on your collected baseline dataset:
```bash
python3 scripts/train_model.py
```
This extracts the 21-dimensional feature vectors, trains the unsupervised model, and serializes the weights to `saved_models/anomaly_model_latest.pkl`. The dashboard server automatically reloads this model!

---

## 6. REST API Reference

The built-in backend provides the following REST endpoints:

| Endpoint | Method | Description |
|---|:---:|---|
| `/api/status` | `GET` | System health, Arduino port, uptime, and latest prediction. |
| `/api/sensors/latest` | `GET` | Latest 10-field telemetry frame and active anomaly score. |
| `/api/sensors/history` | `GET` | Recent 60 telemetry points for charting. |
| `/api/anomalies` | `GET` | History of anomaly events and fault alerts. |
| `/api/recording/start` | `POST` | Starts a named recording session (`session_name`, `mode`). |
| `/api/recording/stop` | `POST` | Stops active recording session and closes dataset file. |
| `/api/health` | `GET` | Service health status. |

---

## 7. Raspberry Pi 5 Auto-Boot Service

To run the monitoring system automatically on system startup:
```bash
sudo cp scripts/servo-monitoring.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable servo-monitoring.service
sudo systemctl start servo-monitoring.service
```
To check service status:
```bash
sudo systemctl status servo-monitoring.service
```
