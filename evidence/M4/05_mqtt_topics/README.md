# Category 05: MQTT Topic Structure & Taxonomy

## 1. Assessment Category
**Category:** 05 — MQTT Topic Architecture, Schema Design & Serialization  
**Assessment Milestone:** Milestone 4 (M4) — Edge AI System Integration  

## 2. Maximum Marks
**Maximum Marks:** `2` / 20

---

## 3. Implementation Summary
The MQTT messaging subsystem implements a clean, extensible, **hierarchical topic taxonomy** matching industrial IoT standards (ISA-95 / Sparkplug B inspired), allowing enterprise SCADA, cloud analytics, and dashboard consumers to selectively subscribe to high-frequency sensor streams, alerts, or node heartbeats.

### Hierarchical Topic Taxonomy:

```text
motor/servo01/
├── sensors/
│   ├── imu       # 3-Axis vibration & acceleration telemetry
│   ├── current   # ACS712 motor current & electrical thresholds
│   ├── voltage   # 0-25V supply rail voltage & brownout status
│   └── audio     # MAX9814 acoustic energy & peak-to-peak noise
├── status        # Commanded angle, actuation state & condition (Retained)
├── alerts        # High-priority threshold alerts & anomaly events (QoS 2)
└── health        # Raspberry Pi edge node heartbeat & metrics (Retained)
```

### Detailed Topic Specifications:
1. `motor/servo01/sensors/imu`:
   - **Payload:** `{"timestamp": "...", "timestamp_ms": 12400, "sensor": "Analog3Axis", "accel_x": 336, "accel_y": 392, "accel_z": 308, "magnitude": 595.6, "unit": "raw_adc_10bit"}`
   - **QoS:** 1 (At least once delivery) | **Retain:** False
2. `motor/servo01/sensors/current`:
   - **Payload:** `{"timestamp": "...", "timestamp_ms": 12400, "sensor": "ACS712_5A", "current_a": 0.092, "unit": "A", "status": "NORMAL", "threshold_a": 0.200}`
   - **QoS:** 1 | **Retain:** False
3. `motor/servo01/sensors/voltage`:
   - **Payload:** `{"timestamp": "...", "timestamp_ms": 12400, "sensor": "VOLTAGE_DIVIDER_5TO1", "voltage_v": 5.02, "unit": "V", "status": "NOMINAL", "nominal_v": 5.0}`
   - **QoS:** 1 | **Retain:** False
4. `motor/servo01/sensors/audio`:
   - **Payload:** `{"timestamp": "...", "timestamp_ms": 12400, "sensor": "MAX9814_MIC", "sound_rms": 16.22, "sound_p2p": 65, "acoustic_status": "NORMAL"}`
   - **QoS:** 1 | **Retain:** False
5. `motor/servo01/status`:
   - **Payload:** `{"timestamp": "...", "servo_id": "servo01", "servo_angle": 90, "state": "NORMAL", "anomaly_score": 0.05, "condition": "NORMAL"}`
   - **QoS:** 1 | **Retain:** True *(Ensures newly connected subscribers immediately know the current servo state)*
6. `motor/servo01/alerts`:
   - **Payload:** `{"timestamp": "...", "severity": "CRITICAL", "channel": "CURRENT_OVERLOAD", "message": "Exceeded 0.200A limit", "metric_value": 0.245, "threshold": 0.200, "device": "rpi5-servo-edge-node01"}`
   - **QoS:** 2 (Exactly once delivery) | **Retain:** False
7. `motor/servo01/health`:
   - **Payload:** `{"timestamp": "...", "node": "Raspberry Pi 5", "uptime_seconds": 3600.0, "total_telemetry_packets": 36000, "arduino_connected": true, "database_healthy": true}`
   - **QoS:** 1 | **Retain:** True

---

## 4. Relevant Source-Code Paths
- [`raspberry_pi/mqtt_client.py`](../../../raspberry_pi/mqtt_client.py) — Publication methods (`publish_imu`, `publish_current`, `publish_voltage`, `publish_audio`, `publish_servo_status`, `publish_alert`, `publish_health`, and `publish_telemetry_frame`).
- [`raspberry_pi/config.py`](../../../raspberry_pi/config.py) — Central topic prefix and `MQTT_TOPICS` dictionary.
- [`tests/test_mqtt_topics.py`](../../../tests/test_mqtt_topics.py) — Automated pytest suite validating topic schema, QoS levels, and frame distribution.

---

## 5. Evidence Included
- **Topic Hierarchy Tree Visualization:**  
  [`screenshots/topic_hierarchy_tree.png`](screenshots/topic_hierarchy_tree.png)  
  *Graphical tree diagram illustrating the 7-topic taxonomy, QoS parameters, and retain flags.*
- **Formal Topic Schema Specification:**  
  [`topic_structure/topic_schema_specification.json`](topic_structure/topic_schema_specification.json)  
  *Machine-readable JSON schema defining data types, required fields, and units for all 7 topics.*
- **Live MQTT Publish & Subscribe Event Stream Log:**  
  [`logs/mqtt_publish_subscribe_stream.log`](logs/mqtt_publish_subscribe_stream.log)  
  *Trace capturing genuine serialized JSON message payloads across all topics.*

---

## 6. Test Procedures
Execute the automated topic suite:
```bash
pytest tests/test_mqtt_topics.py -v -s
```
The test verifies:
1. **Topic Naming Compliance (`test_topic_naming_compliance`):**  
   Asserts exact string match for all 7 specified topics against `motor/servo01/...`.
2. **Payload Schema & Unit Verification (`test_mock_published_payload_schemas`):**  
   Publishes through each method, intercepts the outgoing JSON payload, and verifies required fields (`timestamp`, `unit`, `metric_value`, etc.), correct data types, and designated QoS levels (QoS 2 for alerts, Retain for status/health).
3. **Telemetry Frame Router Distribution (`test_full_frame_router_distribution`):**  
   Ingests a full 10-field telemetry record and verifies synchronous multi-topic dispatch across all 5 telemetry topics.

---

## 7. Actual Results
- **Automated Tests:** 3/3 MQTT Topic tests passed (`tests/test_mqtt_topics.py`).
- **Schema Validation:** 100% of published JSON messages strictly validated against the formal schema with ISO 8601 timestamps and engineering units.
- **QoS Guarantees:** Critical alerts reliably assigned QoS 2; status and node health verified with Retain flags enabled.

---

## 8. Verification Status
🟢 **FULLY IMPLEMENTED AND VALIDATED IN CODEBASE**
- Complete topic schema implemented in `raspberry_pi/mqtt_client.py`.
- Automated router tests verified in `tests/test_mqtt_topics.py`.

---

## 9. Remaining Limitations
- Payload format uses lightweight UTF-8 JSON. For ultra-low bandwidth satellite or cellular IoT links, binary formats (Protocol Buffers or CBOR) could provide further payload size reduction; however, JSON was chosen for broad compatibility with web frontends, Node-RED, and standard MQTT dashboards.

