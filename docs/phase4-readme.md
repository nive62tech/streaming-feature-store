# Phase 4 — Feature Serving API

## What Was Built
- `feature_store/serving/api.py` — FastAPI app with 7 endpoints serving features
  from the Redis online store with sub-millisecond read latency

## Endpoints

| Method | Path | What It Does |
|---|---|---|
| GET | / | API info and endpoint listing |
| GET | /health | Redis + store health check |
| GET | /stats | Row counts, registry size, retraining runs |
| GET | /schema | Registered feature names and types |
| GET | /features/{entity_id} | Latest features for one user from Redis |
| GET | /features/{entity_id}/history | N most recent records from SQLite |
| POST | /features/batch | Features for up to 500 users in one request |
| GET | /retraining/history | Full retraining event log |

## How to Start
- Run: `uvicorn feature_store.serving.api:app --host 0.0.0.0 --port 8000 --reload`
- Swagger UI: http://localhost:8000/docs
- All reads from Redis — no SQLite on the hot path

## Key Decisions
- include_embeddings=False by default — keeps payload small for most use cases
- Batch endpoint uses a loop over Redis reads — Redis pipeline added in Phase 8
- CORS enabled for all origins — dashboard can call API directly
- 404 on missing entity — explicit signal that consumer is not running or user unseen

## Files Created This Phase
- `feature_store/serving/api.py`