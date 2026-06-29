# System Architecture

## Overview

The Streaming Feature Store is a production-grade ML data infrastructure system
consisting of five layers: ingestion, computation, storage, serving, and monitoring.

## Architecture Diagram

Raw Events

│

▼

┌─────────────┐

│ Kafka Topic │  raw-events (3 partitions)

│  Producer   │  Synthetic user click/purchase/view events

└──────┬──────┘

│

▼

┌─────────────────────┐

│   Stream Consumer   │  Reads from raw-events topic

│   Feature Pipeline  │  Windowed aggregations + optional embeddings

└──────┬──────────────┘

│

├──────────────────────────────────┐

▼                                  ▼

┌─────────────┐                  ┌──────────────────┐

│   Redis     │                  │     SQLite       │

│ Online Store│                  │  Offline Store   │

│ (latest     │                  │ (full history,   │

│  features,  │                  │  point-in-time   │

│  sub-ms     │                  │  queries,        │

│  reads)     │                  │  training data)  │

└──────┬──────┘                  └────────┬─────────┘

│                                  │

▼                                  ▼

┌─────────────────┐            ┌──────────────────────┐

│  FastAPI        │            │  Drift Detector      │

│  Serving API    │            │  APScheduler         │

│  /features/     │            │  PSI + KS per        │

│  /batch         │            │  feature every       │

│  /health        │            │  5 minutes           │

│  /schema        │            └──────────┬───────────┘

└─────────────────┘                       │

│ drift > threshold

▼

┌──────────────────────┐

│  Retraining Trigger  │

│  Pull fresh features │

│  Train new model     │

│  Validate accuracy   │

│  Hot-swap if valid   │

│  Update snapshot     │

└──────────┬───────────┘

│

▼

┌──────────────────────┐

│  MLflow Registry     │

│  Versioned artifacts │

│  Active model ptr    │

└──────────────────────┘

│

▼

┌──────────────────────┐

│  React Dashboard     │

│  Drift timeline      │

│  Feature PSI chart   │

│  Model versions      │

│  Retraining log      │

└──────────────────────┘

## Component Breakdown

### Ingestion Layer
- **Kafka Producer** — generates synthetic user events at configurable rate
- **Event Schema** — Pydantic-validated RawEvent with 5 event types
- **Topics** — raw-events (input), computed-features (output), 3 partitions each

### Computation Layer
- **WindowedAggregator** — thread-safe sliding window per user
  - Windows: 1 minute, 5 minutes, 1 hour
  - Stats per window: count, purchase/click/view counts, avg/max price,
    total spend, unique items, unique categories
  - Total: 27 windowed features
- **EventEmbedder** — sentence-transformers all-MiniLM-L6-v2
  - 384-dimensional dense vectors
  - Runs fully on CPU locally
- **FeaturePipeline** — unified entry point, skip_embeddings flag for training

### Storage Layer
- **Online Store (Redis)** — latest feature vector per user, TTL 1hr, sub-ms reads
- **Offline Store (SQLite)** — full feature log, indexed by entity + timestamp
- **Feature Registry (SQLite)** — feature catalog with names, types, versions

### Serving Layer
- **FastAPI** — 10 endpoints, CORS enabled, Pydantic response models
- **Batch endpoint** — up to 500 entities per request
- **History endpoint** — point-in-time feature lookup from SQLite

### Drift Detection Layer
- **PSI (Population Stability Index)** — bin-proportion based drift score
- **KS Test** — non-parametric two-sample distribution test
- **DriftDetector** — runs both tests per feature, saves reports to SQLite
- **APScheduler** — fires drift check every N minutes (default 5)
- **DistributionSnapshot** — reference distribution from training, updatable

### Retraining Layer
- **RetrainingTrigger** — validates conditions, runs full retrain pipeline
- **FeatureTrainer** — GradientBoosting on 27 windowed features
- **ModelRegistry (MLflow)** — versioned runs, active model pointer, hot-swap
- **Zero-downtime swap** — new model fully validated before replacing old one

### Dashboard Layer
- **Next.js 14** — App Router, TypeScript, Tailwind CSS
- **Recharts** — line chart for drift timeline, bar chart for per-feature PSI
- **Auto-refresh** — all components poll API every 30 seconds
- **Action buttons** — trigger drift check and retraining from UI

## Data Flow

Event → Kafka → Consumer → Pipeline → Redis + SQLite

│

Drift Detector (every 5min)

│

PSI + KS vs snapshot

│

Drift > 0.2 → Retrain

│

Validate → Hot-swap → Update snapshot

## Technology Decisions

| Decision | Choice | Reason |
|---|---|---|
| Stream broker | Kafka | Industry standard, partitioned, durable |
| Online store | Redis | Sub-millisecond reads, TTL support |
| Offline store | SQLite | Zero-config, sufficient for single-node |
| Drift metric | PSI + KS | PSI for magnitude, KS for statistical significance |
| Model | GradientBoosting | Strong on tabular, no GPU needed |
| Registry | MLflow local | Full experiment tracking, no server needed |
| Dashboard | Next.js + Recharts | Fast, TypeScript, minimal bundle |