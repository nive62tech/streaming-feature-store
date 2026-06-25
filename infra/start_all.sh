#!/bin/bash
# Master startup script — run from project root in Git Bash
# Usage: bash infra/start_all.sh

echo "================================================"
echo "  Streaming Feature Store — Starting All Services"
echo "================================================"

# 1. Check Redis
echo ""
echo "[1/3] Checking Redis..."
redis-cli ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "  Redis: RUNNING"
else
  echo "  Redis: NOT RUNNING — start Redis service manually"
  exit 1
fi

# 2. Start Kafka + ZooKeeper
echo ""
echo "[2/3] Starting Kafka and ZooKeeper..."
bash infra/kafka_setup.sh

# 3. Activate venv and start FastAPI
echo ""
echo "[3/3] Starting Feature Store API..."
source venv/Scripts/activate
uvicorn feature_store.serving.api:app --host 0.0.0.0 --port 8000 --reload &

echo ""
echo "================================================"
echo "  All services started."
echo "  API running at: http://localhost:8000"
echo "  Kafka broker:   localhost:9092"
echo "  Redis:          localhost:6379"
echo "================================================"