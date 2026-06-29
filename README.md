# Streaming Feature Store with Drift Detection & Auto-Retraining

A production-grade ML data infrastructure system built from scratch.
Kafka ingests raw events → real-time feature computation → features served
via low-latency API → drift detector monitors data distribution continuously →
auto-retrains and hot-swaps models when drift is detected → live React dashboard.

---

## Why This Is Impressive

This is the exact infrastructure that Uber (Michelangelo), Airbnb (Zipline),
LinkedIn (Feathr), and Netflix have spent years building internally.
Companies like Feast, Tecton, and Hopsworks are built entirely around
solving this one problem.

Building it from scratch demonstrates:
- **Streaming data engineering** — Kafka, windowed aggregations, event schemas
- **ML infrastructure thinking** — feature versioning, point-in-time correctness
- **Statistical rigor** — PSI and KS drift detection, not just accuracy monitoring
- **Production systems design** — zero-downtime hot-swap, async retraining
- **Full-stack observability** — live dashboard for features, drift, model lineage

This targets ML Platform, ML Infrastructure, and Applied ML Engineering roles
at Google, Meta, Uber, Anthropic, and similar companies.

---

## Architecture