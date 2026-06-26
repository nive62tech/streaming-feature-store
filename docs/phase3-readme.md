# Phase 3 — Online & Offline Feature Store

## What Was Built
- `feature_store/storage/online_store.py` — Redis-backed store for latest features
  per user. Sub-millisecond reads. Supports single and batch reads via pipeline.
  TTL of 1hr keeps memory bounded. Keys: features:{entity_id}
- `feature_store/storage/offline_store.py` — SQLite store logging every computed
  feature vector. Supports point-in-time range queries and bulk training data pulls.
  Also stores retraining history in a separate table.
- `feature_store/registry.py` — SQLite-backed feature catalog. Tracks all 411
  feature names, types, versions, and descriptions.
- `consumer/stream_consumer.py` — updated to write every computed feature vector
  to both Redis and SQLite after each Kafka message.

## Data Flow
Raw event → Kafka → Consumer → Feature Pipeline → Redis (online) + SQLite (offline)

## How to Verify
- Check Redis keys: `redis-cli keys "features:*"`
- Check offline count: query offline_store.count() in Python
- Check registry: query registry.get_all() in Python

## Key Decisions
- Online store uses JSON serialization — flexible schema, no migrations needed
- Offline store uses SQLAlchemy ORM — easy to swap SQLite for Postgres later
- Both stores are singletons — one connection pool shared across the app
- Registry lives in the same SQLite DB — one file for all metadata

## Files Created or Updated This Phase
- `feature_store/storage/online_store.py` (new)
- `feature_store/storage/offline_store.py` (new)
- `feature_store/registry.py` (new)
- `consumer/stream_consumer.py` (updated)