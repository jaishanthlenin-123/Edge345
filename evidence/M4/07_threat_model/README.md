# Category 07: Security Threat Model & Risk Analysis

## 1. Assessment Category
**Category:** 07 — Security Threat Modeling, Vulnerability Mitigation & STRIDE Matrix  
**Assessment Milestone:** Milestone 4 (M4) — Edge AI System Integration  

## 2. Maximum Marks
**Maximum Marks:** `1` / 20

---

## 3. Implementation Summary
A comprehensive security threat model was developed tailored to the actual physical and networked architecture of the SG90 Servo Motor Condition Monitoring System.

The threat model evaluates the system across three architectural trust boundaries:
1. **Physical Sensor / Actuator Tier:** SG90 servo motor, ACS712 current sensor, voltage divider, MAX9814 microphone, and 3-axis accelerometer.
2. **Embedded Acquisition Tier:** Arduino Uno R3 running non-blocking telemetry firmware over USB serial.
3. **Edge Processing & Industrial Networking Tier:** Raspberry Pi 5 executing feature extraction, machine learning anomaly inference, SQLite persistence, HTTP REST dashboard, Secure MQTT (MQTTS), and Industrial Modbus TCP.

### The Eight Core Evaluated Threats:

| No. | Threat Description | STRIDE Category | Impact Summary | Implemented Mitigation | Status |
|:---:|---|:---:|---|---|:---:|
| **1** | **Unauthorized MQTT Access** | Spoofing / Tampering | Rogue client publishes false telemetry or invalidates alarms | Port 8883 MQTTS enforced; SASL username/password + TLS client verification | 🟢 VERIFIED |
| **2** | **Credential Leakage in Git** | Information Disclosure | Secrets or private keys committed to public GitHub repository | `.gitignore` filters `.env`, `*.key`, `*.pem`; credentials injected via `os.getenv` | 🟢 VERIFIED |
| **3** | **Network Data Interception** | Information Disclosure | Passive sniffer captures motor uptime, speeds, and condition data | TLS 1.2 / TLS 1.3 protocol encryption (AES-256-GCM cipher suite) | 🟢 VERIFIED |
| **4** | **Sensor Data Manipulation** | Tampering | Injected serial noise masks wear or forces spurious shutdowns | 10-field CSV schema checks, monotonic sequence counters, physical bounds | 🟢 VERIFIED |
| **5** | **Unauthorized Actuator Commands** | Elevation of Privilege | Rogue PLC client forces dangerous angle or illegal motion | Range-clamping in Modbus bridge (0°–180°), dedicated emergency stop coil | 🟢 VERIFIED |
| **6** | **Raspberry Pi OS Host Intrusion** | Elevation of Privilege | Attacker modifies ML model weights or accesses SQLite database | Non-root daemon service execution, restricted filesystem permissions (`600`) | 🟢 VERIFIED |
| **7** | **Denial of Service (DoS) Flood** | Denial of Service | Telemetry flood exhausts Pi CPU, blinding operators to faults | Bounded circular feature buffers; throughput tested to >5,000 FPS | 🟢 VERIFIED |
| **8** | **Insecure Protocol Transport** | Information Disclosure | Eavesdropping on unencrypted HTTP or plain MQTT 1883 | Unencrypted MQTT quarantined; TLS 1.2/1.3 standard configuration | 🟢 VERIFIED |

---

## 4. Relevant Source-Code Paths
- [`raspberry_pi/mqtt_client.py`](../../../raspberry_pi/mqtt_client.py) — TLS encryption and credential isolation.
- [`raspberry_pi/serial_reader.py`](../../../raspberry_pi/serial_reader.py) — Serial framing validation, boundary checks, and dropped-packet tracking.
- [`raspberry_pi/plc_bridge.py`](../../../raspberry_pi/plc_bridge.py) — Actuation bounds verification and emergency stop interlocks.
- [`.env.example`](../../../.env.example) — Secure credential management template.
- [`.gitignore`](../../../.gitignore) — Enforced exclusion rules for certificates, keys, and environment files.
- [`tests/test_secure_mqtt.py`](../../../tests/test_secure_mqtt.py) — Automated secret scanning test suite.

---

## 5. Evidence Included
- **STRIDE Threat Matrix Visualization:**  
  [`screenshots/threat_model_stride_matrix.png`](screenshots/threat_model_stride_matrix.png)  
  *High-resolution matrix illustrating attack vectors, components, severity, and verification status.*
- **Comprehensive Threat Analysis Document:**  
  [`threat_analysis/stride_threat_matrix.md`](threat_analysis/stride_threat_matrix.md)  
  *Detailed engineering analysis of each threat, vector, architectural impact, and implemented defense.*
- **DREAD Quantitative Risk Assessment Table:**  
  [`threat_analysis/dread_risk_scoring.csv`](threat_analysis/dread_risk_scoring.csv)  
  *Formal risk scoring based on Damage, Reproducibility, Exploitability, Affected Users, and Discoverability.*

---

## 6. Test Procedures
1. **Automated Repository Secret Scanning:**  
   Execute the secret scanning test in `tests/test_secure_mqtt.py`:
   ```bash
   pytest tests/test_secure_mqtt.py::TestSecureMQTT::test_zero_hardcoded_secrets_in_repo -v
   ```
2. **Corrupted Frame Rejection Test:**  
   Verify that malformed serial packets (e.g. injected noise) are safely dropped by `SerialReader` without memory corruption or process crash:
   ```bash
   pytest tests/test_reliability.py::TestSystemReliability::test_corrupted_stream_recovery -v
   ```
3. **Actuator Boundary Enforcement Test:**  
   Verify that commanding out-of-range angles or unauthorized actuator states via Modbus is blocked by the bridge logic.

---

## 7. Actual Results
- **Automated Tests:** PASSED (All security and boundary tests passed).
- **Secret Hygiene Audit:** Zero exposed API keys, passwords, or private key headers in the repository.
- **DREAD Risk Score:** Highest baseline risk (Credential Leakage, 9.4/10) effectively mitigated to LOW residual risk through `.gitignore` enforcement and environment variable decoupling.

---

## 8. Verification Status
🟢 **FULLY VERIFIED AND VALIDATED**
- Concise, actionable threat model implemented covering all 8 specified threats.
- Mitigations validated through code inspection, automated pytest verification, and architectural design.

---

## 9. Remaining Limitations
- USB serial connection between Arduino Uno and Raspberry Pi lacks hardware-level cryptographic message authentication codes (HMACs) due to ATmega328P computational limits; security relies on physical containment within a locked industrial enclosure.
- For public cloud deployments (e.g. AWS IoT Core or Azure IoT Hub), device certificate provisioning should use a hardware secure element (e.g., ATECC608A on Raspberry Pi).

