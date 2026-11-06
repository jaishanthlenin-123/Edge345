# SG90 Servo Motor Condition Monitoring and Anomaly Detection System

An end-to-end Edge AI & Embedded Condition-Monitoring prototype built with **Arduino Uno** and **Raspberry Pi 5**.

The system monitors an SG90 micro-servo motor across mechanical, electrical, and acoustic domains using multiple sensors, collects structured operational datasets, and employs Machine Learning (Isolation Forest) to detect anomalies and abnormal operating states in real time.

---

## 1. System Architecture

```text
               +-----------------------------+
               |  SG90 Servo Motor Under Test |
               +-----------------------------+
                 |       |           |
       Acoustic  |       | Vibration | Current & Voltage
                 v       v           v
          +---------+ +---------+ +---------------------+
          | MAX9814 | | MPU6050 | | ACS712 & 0-25V Sens |
          +---------+ +---------+ +---------------------+
                 \       |           /
                  \      |          /  Analog & I2C
                   v     v         v
               +-----------------------+
               |      Arduino Uno      |
               | (Actuation & Sampling)|
               +-----------------------+
                           |
                           | USB Serial (115200 Baud)
                           v
               +-----------------------+
               |    Raspberry Pi 5     |
               |   (Host / Edge AI)    |
               +-----------------------+
                 /         |         \
                v          v          v
          +----------+ +--------+ +--------------+
          | Storage  | | Feature| | Unsupervised |
          | & CSV    | | Engine | | ML (IsoForest|
          +----------+ +--------+ +--------------+
                           |
                           v
               +-----------------------+
               | Live Web Dashboard    |
               +-----------------------+
```

---

## 2. Hardware Allocation & Pin Plan

| Component | Proposed Arduino Connection | Function / Domain |
|---|:---:|---|
| **SG90 Servo Signal** | **D9** | PWM Servo Position Control |
| **ACS712 Current Sensor** | **A0** | Motor Current Consumption (Series with +5V) |
| **0–25V Voltage Sensor** | **A1** | Supply Voltage Monitoring (Parallel with +5V) |
| **MAX9814 Microphone** | **A2** | Acoustic Noise / Sound Amplitude |
| **MPU6050 SDA** | **A4** | 6-DOF IMU Vibration (I2C Data) |
| **MPU6050 SCL** | **A5** | 6-DOF IMU Vibration (I2C Clock) |

### Critical Electrical & Power Safety Rules:
1. **Isolated Servo Power:** Never power the SG90 servo motor directly from the Arduino Uno 5V pin! Stalling or sudden movements can draw upwards of 500mA–800mA, causing voltage brownouts, resetting the microcontroller, or damaging onboard regulators.
2. **Common Ground Reference:** Connect the Ground (`GND`) of the external 5V power supply to the Arduino Uno `GND` pin. Without a shared 0V reference, PWM signal voltage levels will float and cause erratic jitter.
3. **ACS712 In-Series Wiring:** The ACS712 Hall-effect sensor must be wired in **series** with the positive supply line of the servo motor.
4. **USB Connection:** Arduino communicates with Raspberry Pi 5 via standard USB Type-A to Type-B cable. Do not connect Arduino 5V GPIO pins directly to Raspberry Pi 3.3V GPIO pins.

---

## 3. Repository Directory Structure

```text
.
├── README.md                           # Master Project Guide
├── PROJECT_STATUS.md                   # Live Tracking & Milestones
├── requirements.txt                    # Python dependencies
├── .gitignore                          # Git ignore rules
│
├── arduino/                            # Embedded Firmware
│   ├── servo_test/                     # Phase 2: Standalone SG90 servo test
│   │   └── servo_test.ino
│   ├── mpu6050_test/                   # Phase 3: Vibration sensor test
│   ├── acs712_test/                    # Phase 3: Current sensor test
│   ├── voltage_sensor_test/            # Phase 3: Voltage divider test
│   ├── max9814_test/                   # Phase 3: Acoustic sensor test
│   └── integrated_firmware/            # Phase 4: Full multi-sensor firmware
│
├── raspberry_pi/                       # Edge Processing & ML
│   ├── config/                         # System & acquisition configurations
│   ├── acquisition/                    # Serial data receiver
│   │   └── serial_receiver.py
│   ├── storage/                        # Dataset persistence utilities
│   ├── preprocessing/                  # Data cleaning and scaling
│   ├── features/                       # Windowed feature extraction
│   ├── models/                         # ML training and evaluation scripts
│   ├── inference/                      # Real-time anomaly scoring
│   └── dashboard/                      # Web-based monitoring UI
│
├── datasets/                           # Collected Telemetry Data
│   ├── raw/                            # Unprocessed CSV logs
│   ├── processed/                      # Extracted feature sets
│   └── experiments/                    # Specific test run folders
│
├── saved_models/                       # Serialized ML models (.joblib / .pkl)
├── results/                            # Evaluation plots, confusion matrices, metrics
├── documentation/                      # Detailed technical documentation
│   ├── architecture.md
│   ├── hardware_connections.md
│   └── sensor_calibration.md
└── evidence/                           # Photos, wiring evidence, serial logs
```

---

## 4. Getting Started: Phase 1 & Phase 2

### Step 1: Raspberry Pi Environment Setup
On your Raspberry Pi 5 terminal, verify Python 3 is installed:
```bash
python3 --version
```
To set up a Python virtual environment (optional but recommended):
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Upload Arduino SG90 Test Program
1. Open the Arduino IDE on your computer / Raspberry Pi.
2. Open `arduino/servo_test/servo_test.ino`.
3. Connect the Arduino Uno via USB.
4. Select board **Arduino Uno** and your serial port (`/dev/ttyACM0` or `/dev/ttyUSB0`).
5. Wire the SG90 servo as documented in [hardware_connections.md](documentation/hardware_connections.md).
6. Upload the sketch.

### Step 3: Start the Raspberry Pi Serial Receiver
Run the acquisition script:
```bash
python3 raspberry_pi/acquisition/serial_receiver.py
```
You will observe live status output showing timestamp, commanded angle, and motor status.

---

## 5. Development Phases Roadmap
- [x] **Phase 1: Environment Setup & Project Architecture**
- [ ] **Phase 2: Servo Motor Standalone Control**
- [ ] **Phase 3: Individual Sensor Testing & Calibration**
- [ ] **Phase 4: Multi-Sensor Integrated Firmware**
- [ ] **Phase 5: Raspberry Pi Data Acquisition**
- [ ] **Phase 6: Baseline & Anomaly Dataset Collection**
- [ ] **Phase 7: Feature Engineering**
- [ ] **Phase 8: Machine Learning Anomaly Detection**
- [ ] **Phase 9: Real-Time Monitoring Dashboard**
- [ ] **Phase 10: Final System Validation & Report**
