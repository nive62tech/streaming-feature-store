# Phase 7 — Auto-Retraining Pipeline

## What Was Built
- `feature_store/retraining/trigger.py` — RetrainingTrigger class handling the
  full retraining flow: should_retrain check, data loading, model training,
  hot-swap validation, artifact saving, MLflow registration, snapshot update,
  and SQLite logging. Thread-safe via _retraining_in_progress flag.
- `scheduler/drift_scheduler.py` — updated to call trigger.run() automatically
  when drift report has trigger_retraining=True. Full pipeline runs on schedule.
- `feature_store/serving/api.py` — two new endpoints:
  POST /retraining/trigger for on-demand retraining from dashboard or CLI,
  GET /retraining/status to check if retraining is currently running.

## Full Auto Pipeline Flow
1. APScheduler fires drift check every 5 minutes
2. DriftDetector pulls last 60 min of features from offline store
3. PSI and KS computed per feature vs training snapshot
4. If max_psi >= 0.2 AND samples >= 100: retraining triggered
5. FeatureTrainer retrains GradientBoosting on all offline store data
6. ModelRegistry validates: new accuracy >= threshold AND >= current accuracy
7. If approved: artifacts saved, MLflow run logged, active pointer updated
8. Reference snapshot updated with new distribution — drift resets
9. Retraining event logged to SQLite retraining_logs table

## Zero-Downtime Hot-Swap
- New model trained fully before replacing old model
- Validation gate: accuracy threshold + must beat current model
- Active model pointer (JSON file) updated atomically
- Old model artifacts kept in models/artifacts/ for rollback
- API reads active pointer on each request — swap is instant

## How to Run
- Full auto pipeline: `python -m scheduler.drift_scheduler`
- Manual retrain via Python: trigger.run(drift_report)
- Manual retrain via API: POST /retraining/trigger?force=true

## Key Decisions
- _retraining_in_progress flag prevents concurrent retraining runs
- Snapshot updated after retraining — drift score resets to near zero
- Rejected models logged to SQLite for full audit trail
- force=true API parameter allows dashboard to bypass sample count check

## Files Created or Updated This Phase
- `feature_store/retraining/trigger.py` (new)
- `scheduler/drift_scheduler.py` (updated)
- `feature_store/serving/api.py` (updated)