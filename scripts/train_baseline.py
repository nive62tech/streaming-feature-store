"""
Baseline training script.

Loads 50,000 seed events from data/raw/events.csv,
computes windowed features for each event,
trains a GradientBoosting classifier,
saves artifacts and registers in MLflow,
saves training distribution snapshot for drift detection.

Run: python scripts/train_baseline.py
"""

import os
import sys
import json
import pickle
import logging
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def compute_distribution_snapshot(df, feature_columns: list) -> dict:
    """
    Compute per-feature statistics from the training set.
    This becomes the reference distribution for drift detection.
    """
    snapshot = {}
    for col in feature_columns:
        if col not in df.columns:
            continue
        values = df[col].fillna(0.0).values.astype(float)
        # Compute histogram with 20 bins
        hist, bin_edges = np.histogram(values, bins=20)
        snapshot[col] = {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "p25": float(np.percentile(values, 25)),
            "p50": float(np.percentile(values, 50)),
            "p75": float(np.percentile(values, 75)),
            "histogram": hist.tolist(),
            "bin_edges": bin_edges.tolist(),
            "n_samples": len(values),
        }
    logger.info(f"Distribution snapshot computed for {len(snapshot)} features.")
    return snapshot


def save_snapshot(snapshot: dict, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(snapshot, f)
    logger.info(f"Snapshot saved to {path}")


def main():
    logger.info("=" * 60)
    logger.info("  Baseline Training Pipeline")
    logger.info("=" * 60)

    # Step 1 — load and compute features from seed CSV
    from feature_store.retraining.trainer import FeatureTrainer, TRAINING_FEATURES
    trainer = FeatureTrainer()

    csv_path = "data/raw/events.csv"
    if not os.path.exists(csv_path):
        logger.error(f"Seed data not found at {csv_path}. Run: python data/seeds/seed_events.py")
        sys.exit(1)

    logger.info("Step 1/5 — Loading and computing features from seed events...")
    df = trainer.load_features_from_csv(csv_path)

    # Step 2 — prepare dataset
    logger.info("Step 2/5 — Preparing dataset...")
    X, y = trainer.prepare_dataset(df)

    # Step 3 — train model
    logger.info("Step 3/5 — Training model...")
    metrics = trainer.train(X, y)
    logger.info(f"Accuracy: {metrics['accuracy']}")
    logger.info(f"Classes: {metrics['classes']}")

    # Step 4 — save artifacts and register in MLflow
    logger.info("Step 4/5 — Saving artifacts and registering in MLflow...")
    version = f"v1_baseline_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    artifact_paths = trainer.save_artifacts(version)

    from feature_store.retraining.model_registry import model_registry
    run_id = model_registry.register(
        trainer=trainer,
        metrics=metrics,
        artifact_paths=artifact_paths,
        version=version,
        tags={"trigger": "baseline", "data_source": "seed_csv"},
    )
    model_registry.set_active(version, run_id, metrics)

    # Step 5 — save training distribution snapshot
    logger.info("Step 5/5 — Saving training distribution snapshot...")
    snapshot = compute_distribution_snapshot(df, TRAINING_FEATURES)
    save_snapshot(snapshot, "data/snapshots/training_distribution.pkl")

    # Save snapshot metadata as JSON for inspection
    snapshot_meta = {
        "version": version,
        "created_at": datetime.utcnow().isoformat(),
        "n_samples": len(df),
        "n_features": len(snapshot),
        "feature_names": list(snapshot.keys()),
        "accuracy": metrics["accuracy"],
    }
    with open("data/snapshots/snapshot_meta.json", "w") as f:
        json.dump(snapshot_meta, f, indent=2)

    logger.info("=" * 60)
    logger.info("  Baseline Training Complete")
    logger.info(f"  Version:  {version}")
    logger.info(f"  Accuracy: {metrics['accuracy']}")
    logger.info(f"  Samples:  {len(df)}")
    logger.info(f"  MLflow run_id: {run_id}")
    logger.info(f"  Snapshot: data/snapshots/training_distribution.pkl")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()