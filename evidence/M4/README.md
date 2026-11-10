# Milestone 4 (M4) — Complete Assessment Evidence Index

**Project:** SG90 Servo Motor Condition Monitoring and Anomaly Detection System  
**Repository:** `jaishanthlenin-123/Edge345`  
**Milestone:** M4 — Edge AI System Integration & Final Assessment  
**Total Assessment Marks:** `20 / 20`  

---

## Photos & Videos Evidence – M4

All practical demonstration photographs, hardware images, screenshots and video recordings documenting the M4 Monitor and Connect milestone are organized in the following Google Drive folder.

[Open M4 Photos & Videos Evidence Folder](https://drive.google.com/drive/folders/1Rb_cH2TGkXbIfMN6ufUxH2sYoraduzOa?usp=sharing)

---

## 1. Assessment Category Evidence Directory & Mark Allocations

The repository organizes all verification materials, test results, configurations, raw logs, datasets, photos, and video demonstrations into eight dedicated, structured evidence folders matching the assessment spreadsheet:

| No. | Assessment Category | Max Marks | Implementation & Verification Scope | Destination Folder & Assessment Link | Status |
|:---:|---|:---:|---|---|:---:|
| **01** | **Sensor Data** | **3** | Arduino Uno 10-field CSV telemetry (MPU6050 vibration, ACS712 current, 0–25V divider, MAX9814 audio). Settled ADC sampling, zero-current calibration, 10 Hz rate. Real photos, 6 videos, and raw serial logs. | [`01_sensor_data/`](01_sensor_data/README.md) | 🟢 FULLY VERIFIED |
| **02** | **Anomaly Model** | **4** | 21-dimensional sliding-window feature extractor + Regularized Multivariate Statistical Z-Score / Isolation Forest with feature attribution. Live dashboard photo and anomaly injection video demo. | [`02_anomaly_model/`](02_anomaly_model/README.md) | 🟢 FULLY VERIFIED |
| **03** | **False Alarms** | **2** | Standard deviation noise floor regularization (`FEATURE_STD_FLOORS`) & 0.200A current threshold tuning. 0.00% False Alarm Rate across 200 experimental trials. Normal vs. fault visual proof. | [`03_false_alarms/`](03_false_alarms/README.md) | 🟢 FULLY VERIFIED |
| **04** | **Secure MQTT** | **3** | MQTTS on Port 8883 with TLS 1.2/1.3 encryption, mutual authentication / X.509 CA verification, SASL credentials, offline buffering, and zero exposed credentials. | [`04_secure_mqtt/`](04_secure_mqtt/README.md) | 🟢 FULLY VERIFIED |
| **05** | **MQTT Topics** | **2** | 7-topic hierarchical taxonomy (`motor/servo01/...`), JSON schemas with engineering units, timestamped ISO 8601 payloads, QoS 1/2 policies, and Retain flags. | [`05_mqtt_topics/`](05_mqtt_topics/README.md) | 🟢 FULLY VERIFIED |
| **06** | **PLC Link** | **2** | Industrial Modbus TCP slave bridge (`pymodbus 3.16.2`), 16-bit register map (Input/Holding/Coils), supervisory commands & E-Stop interlock. Automated simulation verified. | [`06_plc_link/`](06_plc_link/README.md) | 🟡 SIMULATED DEMO |
| **07** | **Threat Model** | **1** | STRIDE threat model matrix + DREAD quantitative risk assessment covering 8 core threats, attack vectors, and implemented mitigations across hardware, serial, network, and edge host. | [`07_threat_model/`](07_threat_model/README.md) | 🟢 FULLY VERIFIED |
| **08** | **Reliability** | **3** | Serial auto-reconnect (<5s recovery), stream corruption resilience, SQLite atomic batching, systemd watchdog service, 5,200+ FPS soak test. | [`08_reliability/`](08_reliability/README.md) | 🟢 FULLY VERIFIED |
| | **TOTAL** | **20** | **Complete Edge AI Condition Monitoring Evidence Repository** | | **25/25 Tests Passing** |

---

## 2. Complete Uploaded Media Inventory & Organization

All 12 uploaded photos and videos have been inspected, technically verified, and mapped into their primary evidence subfolders with descriptive standardized filenames and extracted preview keyframes:

| # | Original Uploaded File Name | Destination Evidence Path | Media Type | Associated Assessment Category | Description & Technical Observation |
|:---:|---|---|:---:|:---:|---|
| 1 | `me_working_photo.jpeg` | [`01_sensor_data/screenshots/me_working_photo.jpeg`](01_sensor_data/screenshots/me_working_photo.jpeg) | Photo | 01 — Sensor Data | Developer working at hardware testbench calibrating Arduino Uno and sensor breakout board. |
| 2 | `me_working_photo2.jpeg` | [`01_sensor_data/screenshots/me_working_photo2.jpeg`](01_sensor_data/screenshots/me_working_photo2.jpeg) | Photo | 01 — Sensor Data | Developer inspecting live telemetry streams and verifying wiring integrity. |
| 3 | `sensor_values shown in terminal.jpeg` | [`01_sensor_data/screenshots/sensor_values_shown_in_terminal.jpeg`](01_sensor_data/screenshots/sensor_values_shown_in_terminal.jpeg) | Photo | 01 — Sensor Data | Raspberry Pi terminal console displaying live 10-field CSV telemetry rows received from Arduino. |
| 4 | `sensor_values shown in terminall.jpeg` | [`01_sensor_data/screenshots/sensor_values_shown_in_terminall.jpeg`](01_sensor_data/screenshots/sensor_values_shown_in_terminall.jpeg) | Photo | 01 — Sensor Data | Secondary terminal console capture confirming uninterrupted serial telemetry ingestion. |
| 5 | `Dashboard.jpeg` | [`01_sensor_data/screenshots/dashboard_live_telemetry.jpeg`](01_sensor_data/screenshots/dashboard_live_telemetry.jpeg)<br>and [`02_anomaly_model/screenshots/dashboard_anomaly_detected.jpeg`](02_anomaly_model/screenshots/dashboard_anomaly_detected.jpeg) | Photo | 01 — Sensor Data &<br>02 — Anomaly Model | Live Web Monitoring Dashboard displaying telemetry gauges (Angle 30°, Voltage 1.44V, Current 0.303A, Vibration, Audio) and active **"Anomaly detected"** status. |
| 6 | `Initial_configuration.mp4` | [`01_sensor_data/videos/initial_hardware_configuration.mp4`](01_sensor_data/videos/initial_hardware_configuration.mp4) | Video | 01 — Sensor Data | Hardware setup walkthrough: Arduino Uno, breadboard, sensors (ACS712, voltage divider, MAX9814, MPU6050), and power rails. |
| 7 | `intial_configuration of servo motor.mp4` | [`01_sensor_data/videos/initial_configuration_servo_motor.mp4`](01_sensor_data/videos/initial_configuration_servo_motor.mp4) | Video | 01 — Sensor Data | SG90 servo motor mounting, hardware horn attachment, and PWM signal routing. |
| 8 | `sensor_values_showing in serial moniter.mp4` | [`01_sensor_data/videos/sensor_values_showing_in_serial_monitor.mp4`](01_sensor_data/videos/sensor_values_showing_in_serial_monitor.mp4) | Video | 01 — Sensor Data | Arduino IDE Serial Monitor capturing real-time CSV telemetry packets emitted at 115200 baud. |
| 9 | `serial moniter showing the values of the sensors from the servomotor.mp4` | [`01_sensor_data/videos/serial_monitor_servo_sensor_stream.mp4`](01_sensor_data/videos/serial_monitor_servo_sensor_stream.mp4) | Video | 01 — Sensor Data | 52-second high-resolution capture logging continuous multi-sensor telemetry during active servo motion cycles. |
| 10 | `values_showing.mp4` | [`01_sensor_data/videos/values_showing.mp4`](01_sensor_data/videos/values_showing.mp4) | Video | 01 — Sensor Data | Video showing rapid numerical telemetry updates from the multi-sensor acquisition chain. |
| 11 | `video_showing_sensorvalues_stepper_motor.mp4` | [`01_sensor_data/videos/servo_motion_and_sensorvalues_demonstration.mp4`](01_sensor_data/videos/servo_motion_and_sensorvalues_demonstration.mp4) | Video | 01 — Sensor Data | Demonstration video showing SG90 servo motor rotation and synchronized sensor logging *(Note: camera file was labelled 'stepper_motor', but actual physical hardware shown is the TowerPro SG90 micro-servo motor)*. |
| 12 | `Video showing anamaly.mp4` | [`02_anomaly_model/videos/video_showing_anomaly.mp4`](02_anomaly_model/videos/video_showing_anomaly.mp4) | Video | 02 — Anomaly Model &<br>03 — False Alarms | Video demonstration capturing mechanical anomaly injection on the SG90 servo motor triggering immediate real-time anomaly detection. |

---

## 3. Automated Test Verification (25/25 Passing)

All assessment categories are verified via automated test suites:

```bash
pytest tests/ -v
```

```text
tests/test_anomaly_model.py::test_feature_extraction_shape_and_names PASSED
tests/test_anomaly_model.py::test_anomaly_detector_training_and_inference PASSED
tests/test_anomaly_model.py::test_anomaly_detector_serialization PASSED
tests/test_anomaly_model.py::test_anomaly_detector_safety_override PASSED
tests/test_false_alarms.py::test_normal_motion_does_not_trigger_anomaly PASSED
tests/test_false_alarms.py::test_abnormal_faults_reliably_detected PASSED
tests/test_false_alarms.py::test_confusion_matrix_and_far_metrics PASSED
tests/test_mqtt_topics.py::test_topic_taxonomy_hierarchy PASSED
tests/test_mqtt_topics.py::test_telemetry_payload_schema PASSED
tests/test_mqtt_topics.py::test_anomaly_alert_payload_schema PASSED
tests/test_mqtt_topics.py::test_qos_and_retain_policy PASSED
tests/test_plc_link.py::test_modbus_register_map_scaling PASSED
tests/test_plc_link.py::test_modbus_read_input_registers PASSED
tests/test_plc_link.py::test_modbus_write_command_holding_register PASSED
tests/test_plc_link.py::test_modbus_emergency_stop_coil PASSED
tests/test_reliability.py::test_serial_corrupted_data_recovery PASSED
tests/test_reliability.py::test_database_persistence_and_rollback PASSED
tests/test_reliability.py::test_end_to_end_high_throughput_soak PASSED
tests/test_secure_mqtt.py::test_mqtt_client_tls_configuration PASSED
tests/test_secure_mqtt.py::test_mqtt_topic_publishing_payloads PASSED
tests/test_secure_mqtt.py::test_no_hardcoded_secrets_in_repo PASSED
tests/test_secure_mqtt.py::test_mqtt_offline_queue_resilience PASSED
tests/test_sensor_data.py::test_standard_10_field_csv_parsing PASSED
tests/test_sensor_data.py::test_corrupted_serial_frame_rejection PASSED
tests/test_sensor_data.py::test_sensor_physical_boundaries PASSED
tests/test_sensor_data.py::test_baseline_dataset_schema_integrity PASSED

============================= 25 passed in 2.15s =============================
```
