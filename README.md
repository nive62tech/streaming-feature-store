@'
# Streaming Feature Store with Drift Detection & Auto-Retraining

A production-grade ML data infrastructure system that ingests real-time events via
Kafka, computes features on the stream, serves them at low latency, monitors for
data distribution drift, and automatically retrains and hot-swaps models when drift
is detected — all observable through a live React dashboard.

---

## Why This Is Impressive

This is the exact infrastructure that Uber (Michelangelo), Airbnb (Zipline),
LinkedIn (Feathr), and Netflix have spent years building. Entire companies —
Feast, Tecton, Hopsworks — are built around solving this single problem.

Building this from scratch demonstrates:
- Streaming data engineering (Kafka, windowed aggregations)
- ML infrastructure thinking (feature versioning, point-in-time correctness)
- Statistical rigor (PSI, KS drift detection — not just accuracy monitoring)
- Production systems design (zero-downtime hot-swap, async retraining, model registry)
- Full-stack observability (live dashboard for features, drift, and model lineage)

---

## Tech Stack

| Layer | Tools |
|---|---|
| Event Streaming | Apache Kafka, kafka-python |
| Online Feature Store | Redis, redis-py |
| Offline Feature Store | SQLite, SQLAlchemy |
| Feature Computation | pandas, numpy, river, sentence-transformers |
| Drift Detection | scipy (KS test), evidently, custom PSI |
| Model Training | scikit-learn, joblib |
| Model Registry | MLflow (local) |
| Serving API | FastAPI, uvicorn |
| Scheduling | APScheduler |
| Dashboard | Next.js 14, React 18, Tailwind CSS, Recharts, ShadCN UI |
| Dev Tools | pytest, black, ruff, python-dotenv |

---

## Folder Structure

streaming-feature-store/

├── README.md

├── .gitignore

├── .env.example

├── requirements.txt

├── requirements-dev.txt

├── docs/

│   ├── phase0-readme.md

│   ├── phase1-readme.md

│   ├── architecture.md

│   ├── drift_detection.md

│   └── api_reference.md

├── infra/

│   ├── start-zookeeper.ps1

│   ├── start-kafka.ps1

│   ├── create-topics.ps1

│   └── verify-infra.ps1

├── data/

│   ├── raw/

│   ├── seeds/seed_events.py

│   └── snapshots/training_distribution.pkl

├── feature_store/

│   ├── config.py

│   ├── registry.py

│   ├── ingestion/producer.py, schemas.py

│   ├── computation/windowed_aggregations.py, embeddings.py, feature_pipeline.py

│   ├── storage/online_store.py, offline_store.py

│   ├── serving/api.py

│   ├── drift/detector.py, metrics.py, snapshot.py

│   └── retraining/trigger.py, trainer.py, model_registry.py

├── consumer/stream_consumer.py

├── scheduler/drift_scheduler.py

├── models/artifacts/

├── tests/

└── dashboard/

---

## Phase Progress

| 0 | Repo & Infra Setup | Folder skeleton, Kafka + Redis local setup, PowerShell scripts, requirements | ✅ Complete |
| 1 | Event Ingestion & Kafka Pipeline | Event schemas, Kafka producer, synthetic data seeding | ✅ Complete |
| 2 | Feature Computation Engine | Windowed aggregations, embeddings, stream consumer | ✅ Complete |
| 3 | Online & Offline Feature Store | Redis online store, SQLite offline store, feature registry | ✅ Complete |
| 4 | Feature Serving API | FastAPI endpoints, low-latency Redis reads, health check | ✅ Complete |
| 5 | Baseline Model & Distribution Snapshot | Baseline model training, MLflow registration, distribution snapshot | ⏳ Pending |
| 6 | Drift Detection Engine | PSI + KS metrics, drift detector, APScheduler drift jobs | ⏳ Pending |
| 7 | Auto-Retraining Pipeline | Drift trigger, retrain on fresh features, zero-downtime hot-swap | ⏳ Pending |
| 8 | React Dashboard | Feature charts, drift timeline, model table, retraining log | ⏳ Pending |
| 9 | Tests, Docs & Final Polish | pytest suite, architecture docs, API reference, final README | ⏳ Pending |

Write-Host "Main README updated."

