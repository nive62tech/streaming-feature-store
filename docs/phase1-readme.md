@'
# Phase 1 — Event Ingestion & Kafka Pipeline

## What Was Built
- `feature_store/config.py` — central settings module, reads all config from .env,
  exposes typed config classes for Kafka, Redis, MLflow, API, Drift, Retraining
- `feature_store/ingestion/schemas.py` — Pydantic RawEvent schema with 5 event types
  (click, purchase, view, search, add_to_cart), validation, and serialization helpers
- `feature_store/ingestion/producer.py` — Kafka producer that generates synthetic
  user events and streams them to the raw-events topic at configurable rate
- `data/seeds/seed_events.py` — seed script that generates 50,000 historical events
  sorted by timestamp and saves to data/raw/events.csv for offline training

## Event Schema
- event_id, event_type, user_id, item_id, category
- price and quantity (for purchase and add_to_cart events)
- session_id, timestamp, platform, region
- 200 synthetic users, 500 synthetic items, 7 categories, 4 regions

## How to Run
- Seed historical data: `python data/seeds/seed_events.py`
- Start live producer: `python -m feature_store.ingestion.producer`
- Producer streams at 2 events/second by default
- Stop with Ctrl+C — closes cleanly

## Key Decisions
- Pydantic schemas enforce type safety at the boundary — bad events never enter the pipeline
- Producer uses acks=all and retries=3 — no events lost on broker hiccup
- Events keyed by user_id — ensures all events for a user go to the same partition
- Event weights are realistic (views and clicks dominate, purchases are rare)

## Files Created This Phase
- `feature_store/config.py`
- `feature_store/ingestion/schemas.py`
- `feature_store/ingestion/producer.py`
- `data/seeds/seed_events.py`
- `data/raw/events.csv` (generated, not committed — in .gitignore)
'@ | Set-Content -Path "docs/phase1-readme.md" -Encoding UTF8

Write-Host "Phase 1 README created."