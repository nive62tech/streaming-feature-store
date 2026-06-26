# Phase 2 — Feature Computation Engine

## What Was Built
- `feature_store/computation/windowed_aggregations.py` — thread-safe sliding window
  aggregator per user over 1min, 5min, 1hr. Computes 9 stats per window (27 total):
  event count, purchase/click/view counts, avg/max price, total spend,
  unique items, unique categories
- `feature_store/computation/embeddings.py` — local sentence-transformers model
  (all-MiniLM-L6-v2, 384 dims, CPU-only) converts event fields to dense vectors
- `feature_store/computation/feature_pipeline.py` — unified pipeline wiring both
  above. Input: one raw event dict. Output: 411-feature flat dict ready for storage
- `consumer/stream_consumer.py` — Kafka consumer that reads raw-events topic,
  runs each message through the pipeline, logs windowed stats every 5 events

## Feature Vector Structure
- 27 windowed aggregation features (9 stats x 3 windows)
- 384 embedding dimensions from all-MiniLM-L6-v2
- Metadata: entity_id, event_id, timestamp, event_type, feature_version
- Total: 414 keys per feature dict

## How to Run
- Start consumer: `python -m consumer.stream_consumer`
- Start producer in another terminal: `python -m feature_store.ingestion.producer`
- Consumer logs feature stats every 5 events

## Key Decisions
- WindowedAggregator uses a thread-safe deque per user — O(1) eviction
- Embedder runs fully locally — no API calls, no GPU needed
- Pipeline is a singleton — model loaded once, reused for every event
- Consumer uses auto_offset_reset=latest — only processes new events in live mode

## Files Created This Phase
- `feature_store/computation/windowed_aggregations.py`
- `feature_store/computation/embeddings.py`
- `feature_store/computation/feature_pipeline.py`
- `consumer/stream_consumer.py`