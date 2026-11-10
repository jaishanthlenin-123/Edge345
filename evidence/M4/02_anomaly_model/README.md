# Category 02: Anomaly Detection Model & Feature Engineering

## 1. Assessment Category
**Category:** 02 — Multivariate Machine Learning Anomaly Detection Pipeline  
**Assessment Milestone:** Milestone 4 (M4) — Edge AI System Integration  

## 2. Maximum Marks
**Maximum Marks:** `4` / 20

---

## 3. Implementation Summary
The edge anomaly detection engine extracts a **21-dimensional multivariate feature space** across sliding time windows of incoming telemetry and executes unsupervised statistical and isolation-based machine learning to detect mechanical binding, gear wear, and electrical overcurrent.

### 1. Sliding Window Feature Extractor (`raspberry_pi/feature_extraction.py`):
- **Window Length:** 10 samples (1.0 second at 10 Hz telemetry rate).
- **Window Step:** 1 sample (90% overlap, yielding an inference evaluation every 100ms).
- **Extracted Feature Vector (21 Dimensions):**
  1. `current_mean`: Window average motor current consumption (Amperes).
  2. `current_peak`: Maximum instantaneous current surge within window.
  3. `current_std`: Current standard deviation (captures rotational load pulsation).
  4. `current_rms`: Root-Mean-Square electrical current.
  5. `voltage_mean`: Average supply rail voltage.
  6. `voltage_std`: Voltage regulation stability.
  7. `voltage_min`: Minimum voltage dip (detects power supply sag).
  8. `voltage_drop`: Peak-to-minimum voltage drop within window ($\max - \min$).
  9. `accel_mag_mean`: Mean 3-axis vibration magnitude ($\sqrt{a_x^2 + a_y^2 + a_z^2}$).
  10. `accel_mag_std`: Vibration amplitude variation across window.
  11. `accel_mag_rms`: RMS mechanical vibration energy.
  12. `accel_mag_p2p`: Peak-to-peak mechanical shock amplitude.
  13. `accel_mag_crest_factor`: Mechanical impulsiveness ($\frac{\text{Peak}}{\text{RMS}}$).
  14. `accel_x_std`: Individual X-axis acceleration dispersion.
  15. `accel_y_std`: Individual Y-axis acceleration dispersion.
  16. `accel_z_std`: Individual Z-axis acceleration dispersion.
  17. `sound_p2p_mean`: Mean acoustic burst peak-to-peak.
  18. `sound_p2p_max`: Maximum acoustic transient noise (gear click/grinding).
  19. `sound_rms_mean`: Mean acoustic energy.
  20. `sound_energy`: Integrated sound power within window.
  21. `angle_motion_rate`: Rate of angular change ($\Delta \theta / \Delta t$).

### 2. Anomaly Detection Model Architecture (`raspberry_pi/models/anomaly_detector.py`):
- **Algorithm:** Regularized Multivariate Statistical Z-Score combined with Isolation Forest.
- **Noise Floor Regularization (`FEATURE_STD_FLOORS`):** Enforces minimum standard deviations across all 21 features during training to prevent division by near-zero variance during static/holding periods.
- **Cross-Domain Multi-Channel Weighting:** Computes composite domain deviations:
  $$\text{Composite } Z = 0.50 \cdot Z_{\text{electrical}} + 0.30 \cdot Z_{\text{vibration}} + 0.20 \cdot Z_{\text{acoustic}}$$
- **Sigmoid Normalization:** Maps composite $Z$-scores to a bounded anomaly score:
  $$\text{Score} = \frac{1}{1 + e^{-1.5 \cdot (Z_{\text{composite}} - 3.0)}} \in [0.00, 1.00]$$
- **Hard Safety Overrides:** Immediate deterministic trip if $I_{\text{peak}} > 0.200\text{A}$ (user limit), $I_{\text{surge}} > 1.2\text{A}$, $V_{\text{min}} < 3.8\text{V}$, or Sound P2P $> 500$.
- **Feature Attribution:** Identifies top-contributing sensor channels responsible for the anomaly trigger.

---

## 4. Relevant Source-Code Paths
- [`raspberry_pi/feature_extraction.py`](../../../raspberry_pi/feature_extraction.py) — 21-dimensional sliding-window signal processing engine.
- [`raspberry_pi/models/anomaly_detector.py`](../../../raspberry_pi/models/anomaly_detector.py) — Calibrated anomaly model with regularized noise floors and feature attribution.
- [`scripts/train_model.py`](../../../scripts/train_model.py) — Offline model training script parsing recorded CSV datasets.
- [`saved_models/anomaly_model_latest.pkl`](../../../saved_models/anomaly_model_latest.pkl) — Production serialized model weights.
- [`saved_models/anomaly_model_latest.json`](../../../saved_models/anomaly_model_latest.json) — Serialized hyperparameter configuration and training metadata.
- [`tests/test_anomaly_model.py`](../../../tests/test_anomaly_model.py) — Automated pytest suite for 21D extraction, inference, overrides, and serialization.

---

## 5. Evidence Included
- **Feature Correlation Heatmap:**  
  [`charts/feature_correlation_heatmap.png`](charts/feature_correlation_heatmap.png)  
  *Depicts Pearson correlation matrix across all 21 condition-monitoring feature dimensions.*
- **Anomaly Score Trajectory Plot:**  
  [`charts/anomaly_score_trajectory.png`](charts/anomaly_score_trajectory.png)  
  *Shows continuous score trajectory transitioning from Normal Operation (0.00–0.28) to Critical Anomaly (0.95) upon induced mechanical stall.*
- **Model Training Metadata Specification:**  
  [`model_results/model_summary.json`](model_results/model_summary.json)  
  *Machine-readable dump of hyperparameters, baseline feature statistics, and regularization floors.*
- **Raspberry Pi 5 Benchmark Evaluation Report:**  
  [`test_results/model_benchmark_report.txt`](test_results/model_benchmark_report.txt)  
  *Quantitative execution latency benchmarks on the target Broadcom BCM2712 CPU.*

---

## 6. Test Procedures
1. **Feature Dimensionality & Integrity Check:**  
   Pass 10 consecutive synthetic telemetry frames to `FeatureExtractor` and assert all 21 named features are computed and contain non-NaN numeric values:
   ```bash
   pytest tests/test_anomaly_model.py -v
   ```
2. **Model Training & Persistence Test:**  
   Train model on 50 samples of simulated baseline feature vectors, serialize to disk (`.pkl` and `.json`), and reload into a fresh instance to assert zero weight degradation.
3. **Deterministic Safety Override Assertion:**  
   Inject anomalous feature dictionaries breaching $I > 0.200\text{A}$ and $V < 3.8\text{V}$; assert that model returns `status == 'ANOMALY'`, `anomaly_score == 0.95`, and identifies `"current_exceeded_0.200A"` in `contributing_features`.
4. **Edge Latency Benchmark:**  
   Measure microsecond execution timing per window extraction and inference step on Raspberry Pi 5.

---

## 7. Actual Results
- **Automated Tests:** 4/4 Anomaly Model unit and integration tests passed (`tests/test_anomaly_model.py`).
- **Feature Extraction Latency:** `0.082 ms` per 10-sample sliding window.
- **Model Inference Latency:** `0.109 ms` per window prediction.
- **Total Pipeline Execution Time:** `0.191 ms` (<0.2% of the available 100ms budget per frame).
- **Throughput Capacity:** >5,200 frames per second theoretical throughput on Raspberry Pi 5.
- **RAM Footprint:** 14.2 MB total (zero specialized GPU or NPU requirement).

---

## 8. Verification Status
🟢 **FULLY VERIFIED AND DEPLOYED**
- 21-feature pipeline verified against actual recorded telemetry (`datasets/normal/`).
- Pre-trained production model weights serialized in `saved_models/` and auto-loaded by the dashboard server on boot.
- Feature attribution verified to accurately pinpoint current surges and acoustic grinding.

---

## 9. Remaining Limitations
- Initial sliding window requires 10 consecutive frames (1.0 second) to prime the circular buffer before the first multivariate feature vector is extracted. During the first second after boot, deterministic single-sample rule checks safeguard the motor.
- The model is currently trained on unloaded free-motion baseline data. If a permanent mechanical payload is permanently mounted on the servo arm, the baseline dataset must be re-collected using `./scripts/collect_dataset.sh normal 60` and re-trained with `python3 scripts/train_model.py`.
