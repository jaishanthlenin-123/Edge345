#!/usr/bin/env python3
"""
Unit and Integration Tests for Category 02: Anomaly Detection Model
Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
Target: Raspberry Pi 5 Edge Machine Learning Pipeline
"""

import sys
import pytest
import numpy as np
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from raspberry_pi.feature_extraction import FeatureExtractor, FEATURE_COLUMNS
from raspberry_pi.models.anomaly_detector import AnomalyDetectionModel
from raspberry_pi.config import SAVED_MODELS_DIR


class TestAnomalyDetectionPipeline:
    """Tests 21D feature extraction, model inference, safety overrides, and serialization."""

    @pytest.fixture
    def feature_extractor(self):
        return FeatureExtractor(window_size=10)

    @pytest.fixture
    def model(self):
        return AnomalyDetectionModel()

    def test_21d_feature_extraction(self, feature_extractor):
        """Verifies extraction of all 21 statistical, vibration, acoustic, and electrical features."""
        # Feed 10 synthetic frames to fill the sliding window
        features = None
        for i in range(10):
            frame = {
                "timestamp_ms": i * 100,
                "sequence": i,
                "servo_angle": 90 if i < 5 else 150,
                "voltage_v": 5.0 + (i % 2) * 0.05,
                "current_a": 0.090 + (i % 3) * 0.015,
                "accel_x": 335 + i,
                "accel_y": 390 - i,
                "accel_z": 308 + (i % 2),
                "sound_rms": 14.0 + i * 0.5,
                "sound_p2p": 50 + i * 2
            }
            features = feature_extractor.update(frame)

        assert features is not None, "Feature window failed to produce output after 10 samples"
        assert len(features) == len(FEATURE_COLUMNS), f"Expected {len(FEATURE_COLUMNS)} features, got {len(features)}"
        for col in FEATURE_COLUMNS:
            assert col in features, f"Feature {col} missing from extracted features"
            assert isinstance(features[col], (float, int)), f"Feature {col} is non-numeric"

    def test_model_training_and_serialization(self, model, tmp_path):
        """Verifies training on baseline feature matrix, persistence, and loading."""
        np.random.seed(42)
        # 50 normal window samples with 21 features
        dummy_X = np.random.normal(loc=0.0, scale=1.0, size=(50, len(FEATURE_COLUMNS)))
        # Scale to realistic ranges
        dummy_X[:, 0] = np.random.uniform(0.06, 0.12, 50)  # current_mean
        dummy_X[:, 4] = np.random.uniform(4.90, 5.10, 50)  # voltage_mean

        metadata = model.train(dummy_X, FEATURE_COLUMNS)
        assert model.is_trained is True
        assert metadata["sample_count"] == 50

        # Save model
        save_path = tmp_path / "test_model.pkl"
        model.save(save_path)
        assert save_path.exists()
        assert save_path.with_suffix(".json").exists()

        # Load model back
        loaded = AnomalyDetectionModel.load(save_path)
        assert loaded.is_trained is True
        assert len(loaded.baseline_stats) == len(FEATURE_COLUMNS)

    def test_critical_safety_overrides(self, model):
        """Verifies hard physical safety limits immediately trigger ANOMALY (Score 0.95)."""
        # Train minimal baseline
        dummy_X = np.ones((5, len(FEATURE_COLUMNS))) * 0.1
        model.train(dummy_X, FEATURE_COLUMNS)

        # 1. Overcurrent (> 0.200A)
        overcurrent_features = {col: 0.1 for col in FEATURE_COLUMNS}
        overcurrent_features["current_mean"] = 0.250
        overcurrent_features["current_peak"] = 0.280

        pred = model.predict_window(overcurrent_features)
        assert pred["status"] == "ANOMALY"
        assert pred["is_anomaly"] is True
        assert pred["anomaly_score"] >= 0.95

        # 2. Voltage brownout (< 3.8V)
        brownout_features = {col: 0.1 for col in FEATURE_COLUMNS}
        brownout_features["voltage_min"] = 3.20

        pred_brown = model.predict_window(brownout_features)
        assert pred_brown["status"] == "ANOMALY"
        assert pred_brown["is_anomaly"] is True

    def test_saved_production_model_exists(self):
        """Verifies the actual pre-trained production model exists in saved_models/."""
        prod_model_pkl = SAVED_MODELS_DIR / "anomaly_model_latest.pkl"
        prod_model_json = SAVED_MODELS_DIR / "anomaly_model_latest.json"

        assert prod_model_pkl.exists(), f"Production model missing: {prod_model_pkl}"
        assert prod_model_json.exists(), f"Production model metadata missing: {prod_model_json}"

        loaded = AnomalyDetectionModel.load(prod_model_pkl)
        assert loaded.is_trained is True
        assert len(loaded.baseline_stats) == 21

