# Phase 6 — Drift Detection Engine

## What Was Built
- `feature_store/drift/metrics.py` — PSI and KS test implementations from scratch.
  PSI measures distribution shift using bin proportions. KS test measures max CDF
  difference. Both run per feature across all 27 windowed aggregation features.
- `feature_store/drift/snapshot.py` — loads training reference distribution from
  pickle snapshot. Reconstructs reference sample values from stored histograms.
  Supports in-place update after retraining.
- `feature_store/drift/detector.py` — pulls live features from offline store,
  runs PSI and KS per feature, aggregates into drift report, saves to SQLite
  drift_reports table. Signals retraining when max PSI >= threshold.
- `scheduler/drift_scheduler.py` — APScheduler blocking scheduler that runs drift
  checks every N minutes (configured via .env). Runs an immediate check on startup.
- 4 new API endpoints: /drift/latest, /drift/history, /drift/check, /drift/snapshot

## Drift Thresholds
- PSI < 0.1  — no drift
- PSI < 0.2  — moderate drift, monitor
- PSI >= 0.2 — severe drift, triggers retraining
- KS p < 0.05 — statistically significant distribution shift

## How to Run
- Manual check: `python -c "from feature_store.drift.detector import detector; print(detector.run_check())"`
- Scheduled: `python -m scheduler.drift_scheduler`
- On-demand via API: POST /drift/check

## Key Decisions
- PSI uses reference bin edges — consistent binning across checks
- KS test is non-parametric — works for any distribution shape
- Drift reports stored in SQLite — full history queryable from dashboard
- Scheduler runs immediate check on startup — no waiting for first interval
- Drift simulation via injected high-price purchase events for easy testing

## Files Created This Phase
- `feature_store/drift/metrics.py`
- `feature_store/drift/snapshot.py`
- `feature_store/drift/detector.py`
- `scheduler/drift_scheduler.py`
- Updated `feature_store/serving/api.py`