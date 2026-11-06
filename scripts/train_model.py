#!/usr/bin/env python3
"""
Model Training Script for Unsupervised Anomaly Detection
Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
Target: Raspberry Pi 5

Usage:
    python3 scripts/train_model.py [--dataset path/to/normal_data.csv]
"""

import sys
import argparse
import numpy as np
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from raspberry_pi.config import NORMAL_DATA_DIR, RAW_DATA_DIR, SAVED_MODELS_DIR
from raspberry_pi.feature_extraction import extract_features_from_csv, FEATURE_COLUMNS
from raspberry_pi.models.anomaly_detector import AnomalyDetectionModel


def train_on_dataset(csv_path: Optional[str] = None):
    # Locate dataset
    if csv_path:
        target_csv = Path(csv_path)
    else:
        # Search normal data directory first, fallback to raw
        candidates = list(NORMAL_DATA_DIR.glob("*.csv")) + list(RAW_DATA_DIR.glob("*.csv"))
        if not candidates:
            print("[ERROR] No CSV datasets found in datasets/normal/ or datasets/raw/.")
            print("Please record normal operation data first via: python3 raspberry_pi/data_logger.py")
            sys.exit(1)
        target_csv = candidates[0]

    print("=" * 80)
    print(f" TRAINING ANOMALY DETECTION MODEL")
    print(f" Source Dataset: {target_csv.resolve()}")
    print("=" * 80)

    # Extract windowed features
    feature_rows = extract_features_from_csv(str(target_csv), window_size=10, step_size=2)
    if not feature_rows:
        print("[ERROR] Not enough records in CSV to form feature windows.")
        sys.exit(1)

    print(f"[FEATURES] Extracted {len(feature_rows)} feature windows ({len(FEATURE_COLUMNS)} dimensions each).")

    # Form feature matrix
    X = np.array([[row[col] for col in FEATURE_COLUMNS] for row in feature_rows], dtype=np.float64)

    # Train model
    model = AnomalyDetectionModel(model_type="auto", contamination=0.05)
    meta = model.train(X, feature_names=FEATURE_COLUMNS)

    # Save model
    save_path = SAVED_MODELS_DIR / "anomaly_model_latest.pkl"
    model.save(save_path)

    print("\n" + "-" * 80)
    print(" TRAINING SUMMARY & METRICS")
    print("-" * 80)
    print(f" Model Type       : {meta['model_type'].upper()}")
    print(f" Training Samples : {meta['sample_count']} windows")
    print(f" Features Used    : {len(meta['feature_names'])}")
    print(f" Saved Model Path : {save_path.resolve()}")
    print(f" Metadata JSON    : {save_path.with_suffix('.json').resolve()}")
    print("=" * 80)
    print("[SUCCESS] Model trained and deployed for real-time inference.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Servo Anomaly Detection Model")
    parser.add_argument("--dataset", type=str, default=None, help="Path to normal operating CSV dataset")
    args = parser.parse_args()
    train_on_dataset(args.dataset)
