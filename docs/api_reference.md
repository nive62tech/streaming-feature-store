# API Reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

---

## System Endpoints

### GET /
Returns API info and list of all endpoints.

### GET /health
Returns health status of all backing services.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T00:00:00",
  "redis": "ok",
  "offline_store_rows": 1234,
  "registry_features": 411
}
```

### GET /stats
Returns store statistics.

**Response:**
```json
{
  "offline_store_rows": 1234,
  "registry_features": 411,
  "retraining_runs": 3,
  "timestamp": "2024-01-01T00:00:00"
}
```

---

## Feature Endpoints

### GET /features/{entity_id}
Get the latest feature vector for one user from Redis.

**Parameters:**
- `entity_id` (path) — user ID e.g. user_0042
- `include_embeddings` (query, default false) — include 384-dim embedding

**Response:**
```json
{
  "entity_id": "user_0042",
  "timestamp": "2024-01-01T00:00:00",
  "event_type": "click",
  "feature_version": "v1",
  "ttl_seconds": 3541,
  "found": true,
  "features": {
    "event_count_1min": 3,
    "event_count_5min": 7,
    "avg_price_5min": 124.5
  }
}
```

**Errors:**
- `404` — entity not found in Redis

### POST /features/batch
Get features for multiple entities in one request.

**Body:**
```json
{
  "entity_ids": ["user_0001", "user_0002"],
  "include_embeddings": false
}
```

**Response:**
```json
{
  "results": [...],
  "found_count": 1,
  "missing_count": 1,
  "total_requested": 2
}
```

**Errors:**
- `400` — batch size exceeds 500

### GET /features/{entity_id}/history
Get N most recent feature records from SQLite offline store.

**Parameters:**
- `limit` (query, default 10, max 100)

---

## Schema Endpoints

### GET /schema
Get registered feature schema.

**Parameters:**
- `limit` (query, default 50)
- `exclude_embeddings` (query, default true)

---

## Drift Endpoints

### GET /drift/latest
Get the most recent drift check report with per-feature results.

**Errors:**
- `404` — no drift reports yet

### GET /drift/history
Get recent drift check summary rows.

**Parameters:**
- `limit` (query, default 20, max 200)

### POST /drift/check
Manually trigger a drift check on demand.

**Parameters:**
- `window_minutes` (query, default 60)

### GET /drift/snapshot
Get metadata about the current reference distribution snapshot.

---

## Model Endpoints

### GET /model/active
Get the currently active model version and its metrics.

### GET /model/versions
List all MLflow model versions.

---

## Retraining Endpoints

### GET /retraining/history
Get full retraining event log from SQLite.

### GET /retraining/status
Check if retraining is currently in progress.

### POST /retraining/trigger
Manually trigger the retraining pipeline.

**Parameters:**
- `force` (query, default false) — bypass sample count check

**Response:**
```json
{
  "status": "success",
  "version": "v_retrain_20240101_000000",
  "accuracy_before": 0.72,
  "accuracy_after": 0.75,
  "accuracy_delta": 0.03,
  "n_samples": 1500,
  "duration_seconds": 42.1
}
```

**Errors:**
- `409` — retraining already in progress
- `400` — insufficient samples (use force=true to override)