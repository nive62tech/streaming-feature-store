# Phase 5 — Baseline Model & Training Distribution Snapshot

## What Was Built
- `feature_store/retraining/trainer.py` — FeatureTrainer class handling feature
  loading from CSV or offline store, dataset preparation, GradientBoosting training,
  artifact saving and loading, and single-event prediction
- `feature_store/retraining/model_registry.py` — MLflow-backed model registry with
  versioning, active model pointer, and hot-swap validation logic
- `scripts/train_baseline.py` — end-to-end baseline training script: loads 50k seed
  events, computes features, trains model, registers in MLflow, saves distribution
  snapshot
- `data/snapshots/training_distribution.pkl` — per-feature statistics (mean, std,
  min, max, percentiles, histogram) used as reference for drift detection
- New API endpoints: GET /model/active and GET /model/versions

## Training Details
- Model: GradientBoostingClassifier (100 estimators, depth 4)
- Features: 27 windowed aggregation features (no embeddings for speed)
- Target: event_type (5 classes: click, purchase, view, search, add_to_cart)
- Train/test split: 80/20
- Tracked in MLflow local at ./mlruns

## How to Retrain
- Run: `python scripts/train_baseline.py`
- New version auto-tagged with timestamp
- Active model pointer updated in models/artifacts/active_model.json

## Key Decisions
- Embeddings excluded from training — 384 dims slow to train on CPU, windowed
  features carry enough signal for event type classification
- Snapshot stores per-feature histograms — enables PSI computation in Phase 6
- Hot-swap validates accuracy before replacing active model — no regressions
- MLflow runs locally — no server needed, artifacts in ./mlruns folder

## Files Created This Phase
- `feature_store/retraining/trainer.py`
- `feature_store/retraining/model_registry.py`
- `scripts/train_baseline.py`
- `data/snapshots/training_distribution.pkl` (generated)
- `data/snapshots/snapshot_meta.json` (generated)
- `models/artifacts/active_model.json` (generated)