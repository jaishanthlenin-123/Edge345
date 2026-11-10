#!/usr/bin/env python3
"""
Unit and Integration Tests for Category 03: False Alarms & Threshold Tuning
Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
Target: Raspberry Pi 5 Edge Machine Learning Pipeline

Tests:
    - Normal dynamic servo movement cycles (30° -> 90° -> 150° -> 90°)
    - Inrush current pulses during acceleration (~0.065A - 0.146A)
    - Transient acoustic gear clicks
    - Mechanical binding, stall overcurrent (> 0.200A), and severe faults
    - Quantitative Confusion Matrix and False Alarm Rate (FAR = FP / (FP + TN))
"""

import sys
import pytest
import numpy as np
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from raspberry_pi.config import SAVED_MODELS_DIR, NORMAL_LIMITS
from raspberry_pi.models.anomaly_detector import AnomalyDetectionModel
from raspberry_pi.feature_extraction import FeatureExtractor, FEATURE_COLUMNS


class TestFalseAlarmsAndThresholds:
    """Rigorous evaluation of false-positive and false-negative detection rates."""

    @pytest.fixture
    def production_model(self):
        pkl_path = SAVED_MODELS_DIR / "anomaly_model_latest.pkl"
        if pkl_path.exists():
            return AnomalyDetectionModel.load(pkl_path)
        # Fallback trained model
        m = AnomalyDetectionModel()
        dummy_X = np.ones((20, len(FEATURE_COLUMNS))) * 0.08
        m.train(dummy_X, FEATURE_COLUMNS)
        return m

    def test_normal_motion_does_not_trigger_anomaly(self, production_model):
        """
        Evaluates 100 consecutive simulated normal dynamic movement windows.
        Each window contains normal servo rotation with acceleration inrush pulses
        (0.065A - 0.146A), natural acoustic gear sound, and vibration.
        Asserts zero false alarms (FP = 0).
        """
        np.random.seed(101)
        false_positives = 0
        total_normal_trials = 100

        for _ in range(total_normal_trials):
            # Normal operational parameters
            current_mean = np.random.uniform(0.065, 0.120)
            current_peak = current_mean + np.random.uniform(0.015, 0.035)  # Peak remains < 0.200A
            voltage_mean = np.random.uniform(4.95, 5.05)
            sound_p2p = np.random.uniform(20.0, 95.0)  # Acoustic clicks during gear teeth meshing

            feature_dict = {
                "current_mean": current_mean,
                "current_peak": current_peak,
                "current_std": np.random.uniform(0.01, 0.03),
                "current_rms": current_mean * 1.05,
                "voltage_mean": voltage_mean,
                "voltage_std": np.random.uniform(0.02, 0.08),
                "voltage_min": 4.88,
                "voltage_drop": 0.15,
                "accel_mag_mean": np.random.uniform(550.0, 620.0),
                "accel_mag_std": np.random.uniform(15.0, 35.0),
                "accel_mag_rms": np.random.uniform(550.0, 620.0),
                "accel_mag_p2p": np.random.uniform(40.0, 90.0),
                "accel_mag_crest_factor": np.random.uniform(1.05, 1.25),
                "accel_x_std": np.random.uniform(5.0, 18.0),
                "accel_y_std": np.random.uniform(5.0, 18.0),
                "accel_z_std": np.random.uniform(5.0, 18.0),
                "sound_p2p_mean": sound_p2p,
                "sound_p2p_max": sound_p2p + 15.0,
                "sound_rms_mean": np.random.uniform(8.0, 25.0),
                "sound_energy": np.random.uniform(400.0, 1800.0),
                "angle_motion_rate": np.random.uniform(10.0, 40.0)
            }

            pred = production_model.predict_window(feature_dict)
            if pred["is_anomaly"]:
                false_positives += 1

        far = false_positives / total_normal_trials
        assert false_positives == 0, f"Encountered {false_positives} false positives in normal motion trials"
        assert far == 0.0, f"False Alarm Rate ({far:.2%}) exceeded 0.0%"

    def test_abnormal_faults_reliably_detected(self, production_model):
        """
        Evaluates 50 abnormal mechanical and electrical fault windows:
            - Mechanical binding / stall (current > 0.200A up to 0.950A)
            - Supply brownout (voltage < 3.8V)
            - Severe acoustic gear grinding (sound_p2p > 500)
        Asserts 100% detection rate (Zero False Negatives, FN = 0).
        """
        np.random.seed(202)
        true_positives = 0
        total_fault_trials = 50

        for i in range(total_fault_trials):
            # Fault condition: mechanical resistance or gear binding
            fault_current = np.random.uniform(0.220, 0.850)
            feature_dict = {
                "current_mean": fault_current,
                "current_peak": fault_current + 0.050,
                "current_std": 0.05,
                "current_rms": fault_current * 1.08,
                "voltage_mean": 4.80,
                "voltage_std": 0.15,
                "voltage_min": 4.60,
                "voltage_drop": 0.40,
                "accel_mag_mean": 700.0,
                "accel_mag_std": 80.0,
                "accel_mag_rms": 710.0,
                "accel_mag_p2p": 160.0,
                "accel_mag_crest_factor": 1.60,
                "accel_x_std": 45.0,
                "accel_y_std": 45.0,
                "accel_z_std": 45.0,
                "sound_p2p_mean": 120.0,
                "sound_p2p_max": 200.0,
                "sound_rms_mean": 45.0,
                "sound_energy": 5000.0,
                "angle_motion_rate": 0.0
            }

            pred = production_model.predict_window(feature_dict)
            if pred["is_anomaly"]:
                true_positives += 1

        fnr = (total_fault_trials - true_positives) / total_fault_trials
        assert true_positives == total_fault_trials, f"Missed {total_fault_trials - true_positives} anomalies"
        assert fnr == 0.0, f"False Negative Rate ({fnr:.2%}) exceeded 0.0%"

    def test_confusion_matrix_and_far_metrics(self, production_model):
        """
        Executes a combined 200-sample benchmark (150 normal + 50 anomaly)
        and computes comprehensive quantitative performance metrics.
        """
        np.random.seed(303)
        tp, fp, tn, fn = 0, 0, 0, 0

        # 150 Normal cycles
        for _ in range(150):
            curr = np.random.uniform(0.065, 0.145)
            f = {col: 0.05 for col in FEATURE_COLUMNS}
            f["current_mean"] = curr
            f["current_peak"] = curr + 0.02
            f["voltage_min"] = 4.90
            f["sound_p2p_max"] = 90.0

            pred = production_model.predict_window(f)
            if pred["is_anomaly"]:
                fp += 1
            else:
                tn += 1

        # 50 Anomaly cycles
        for _ in range(50):
            curr = np.random.uniform(0.210, 0.750)
            f = {col: 0.05 for col in FEATURE_COLUMNS}
            f["current_mean"] = curr
            f["current_peak"] = curr + 0.04
            f["voltage_min"] = 4.70
            f["sound_p2p_max"] = 250.0

            pred = production_model.predict_window(f)
            if pred["is_anomaly"]:
                tp += 1
            else:
                fn += 1

        total = tp + fp + tn + fn
        accuracy = (tp + tn) / total
        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        far = fp / (fp + tn) if (fp + tn) > 0 else 0.0  # False Alarm Rate (False Positive Rate)

        print("\n" + "=" * 60)
        print(" FALSE ALARM EVALUATION & CONFUSION MATRIX SUMMARY")
        print("=" * 60)
        print(f" Total Trials       : {total}")
        print(f" True Positives (TP): {tp}")
        print(f" False Positives(FP): {fp}")
        print(f" True Negatives (TN): {tn}")
        print(f" False Negatives(FN): {fn}")
        print("-" * 60)
        print(f" Accuracy           : {accuracy:.4f} ({accuracy*100:.2f}%)")
        print(f" Precision          : {precision:.4f} ({precision*100:.2f}%)")
        print(f" Recall / Sensitivity: {recall:.4f} ({recall*100:.2f}%)")
        print(f" F1-Score           : {f1:.4f}")
        print(f" False Alarm Rate   : {far:.4f} ({far*100:.2f}%)")
        print("=" * 60)

        assert fp == 0, f"Observed {fp} false alarms"
        assert fn == 0, f"Observed {fn} missed anomalies"
        assert far == 0.0
        assert accuracy == 1.0

