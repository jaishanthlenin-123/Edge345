# Project Status: SG90 Servo Motor Anomaly Detection System

**Last Updated:** November 6, 2026  
**Current Phase:** Phase 1 (Development Environment) & Phase 2 (Servo Motor Control Preparation)  
**System Target:** Arduino Uno (Signal & Acquisition) + Raspberry Pi 5 (Processing, ML, Dashboard)

---

## 1. Development Phases Overview

| Phase | Description | Status | Evidence / Notes |
|:---:|---|:---:|---|
| **Phase 1** | **Development Environment** | 🟡 In Progress | Directory structure initialized, git repository set up, requirements defined. Python virtual environment to be activated. Arduino toolchain verification pending. |
| **Phase 2** | **Servo Motor Control** | 🟡 In Progress | Standalone test sketch `arduino/servo_test/servo_test.ino` prepared. Hardware wiring & safety review ready for execution. |
| **Phase 3** | **Individual Sensor Testing** | ⚪ Not Started | Awaiting physical verification of MPU6050, ACS712, Voltage Sensor, MAX9814. |
| **Phase 4** | **Integrated Arduino Firmware** | ⚪ Not Started | Will combine individual tested sensor routines into unified non-blocking CSV streamer. |
| **Phase 5** | **Raspberry Pi Data Acquisition** | 🟡 In Progress | Serial receiver skeleton `raspberry_pi/acquisition/serial_receiver.py` created. |
| **Phase 6** | **Dataset Collection** | ⚪ Not Started | Normal baseline vs. experimental operating condition protocols to be defined. |
| **Phase 7** | **Feature Engineering** | ⚪ Not Started | Time-domain (RMS, P2P, variance) and contextual angle features planned. |
| **Phase 8** | **Machine Learning** | ⚪ Not Started | Isolation Forest baseline model for unsupervised anomaly scoring. |
| **Phase 9** | **Live Monitoring Dashboard** | ⚪ Not Started | Web dashboard (Flask) displaying live telemetry, anomaly scores, and sensor states. |
| **Phase 10** | **Final Integration & Testing** | ⚪ Not Started | Full pipeline end-to-end verification and final validation report. |

*Status Legend:* ⚪ Not Started | 🟡 In Progress | 🟢 Completed | 🔴 Blocked

---

## 2. Hardware Inventory & Verification Checklist

| Component | Function | Proposed Arduino Pin | Verification Status | Notes / Safety Constraints |
|---|---|:---:|:---:|---|
| **Arduino Uno** | Microcontroller | - | 🟡 Awaiting Connection | Connects via USB to Raspberry Pi 5. Powers its own ATmega328P. |
| **Raspberry Pi 5** | Host / Edge Processor | - | 🟢 Online | aarch64 Debian Trixie (Kernel 6.18.50+rpt-rpi-2712). |
| **SG90 Servo** | Actuator Under Test | D9 (PWM) | ⚪ Unverified | **CRITICAL:** Requires external dedicated 5V power supply. Never power SG90 directly from Arduino 5V pin! |
| **MPU6050** | 6-DOF IMU (Vibration/Motion) | A4 (SDA), A5 (SCL) | ⚪ Unverified | Check breakout operating voltage (5V with onboard LDO vs 3.3V). I2C bus at 100kHz / 400kHz. |
| **ACS712** | Current Sensor | A0 | ⚪ Unverified | Place in series with servo positive supply rail. Module variant (5A, 20A, or 30A) must be confirmed. |
| **0–25V Voltage Sensor** | Motor Supply Monitor | A1 | ⚪ Unverified | Parallel connection across servo power rail. Resistor divider (5:1 ratio: 30kΩ / 7.5kΩ). Max input 25V produces 5V to ADC. |
| **MAX9814** | Microphone / Acoustic | A2 | ⚪ Unverified | Connect OUT to A0-A3 ADC. Check gain pin (Gain: VDD=40dB, GND=50dB, Float=60dB). |
| **Breadboard & Wires** | Prototyping Interconnect | - | ⚪ Unverified | High-current servo power leads should bypass flimsy breadboard rails where possible. |

---

## 3. Strict Hardware Safety Rules

1. **Common Ground:** Arduino GND, external 5V servo supply negative, and all sensor ground pins **MUST** be connected together to provide a common 0V voltage reference.
2. **Servo Power Isolation:** The SG90's red wire (+5V) connects **ONLY** to the external 5V DC power supply positive terminal, never to Arduino's 5V pin. The Arduino voltage regulator cannot handle inductive current spikes from servo motor stalls (which can pull over 500mA–800mA and reset the microcontroller or burn the onboard regulator).
3. **No Direct 5V GPIO to Pi:** Do not connect Arduino 5V digital pins directly to Raspberry Pi 3.3V GPIO headers. Communication is strictly over the USB cable via serial port (`/dev/ttyACM*` or `/dev/ttyUSB*`).
4. **Inspect Before Power:** No circuit will be energized until wiring is verified step-by-step.

---

## 4. Current Workspace Files

- `PROJECT_STATUS.md`: This comprehensive tracking document.
- `README.md`: Project overview and operational guide.
- `requirements.txt`: Python dependencies for Raspberry Pi 5.
- `.gitignore`: Clean git exclusions for compiled code, venv, and large media.
- `arduino/servo_test/servo_test.ino`: Standalone Phase 2 test sketch for SG90 servo motor.
- `raspberry_pi/acquisition/serial_receiver.py`: Modular Python serial listener and CSV logger.
- `documentation/hardware_connections.md`: Detailed wiring pinouts and power distribution scheme.
- `documentation/architecture.md`: Complete data flow and interface specifications.
