import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import pickle
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from feature_store.storage.online_store import online_store
from feature_store.storage.offline_store import offline_store
from feature_store.registry import registry
from feature_store.config import settings
from feature_store.retraining.model_registry import model_registry
from feature_store.drift.detector import detector
from feature_store.drift.snapshot import snapshot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Streaming Feature Store API",
    description="Low-latency feature serving API backed by Redis online store.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# Request / Response Models
# --------------------------------------------------------------------------

class BatchRequest(BaseModel):
    entity_ids: List[str]
    include_embeddings: bool = False


class FeatureResponse(BaseModel):
    entity_id: str
    timestamp: Optional[str]
    event_type: Optional[str]
    feature_version: Optional[str]
    ttl_seconds: int
    features: Dict[str, Any]
    found: bool


class BatchResponse(BaseModel):
    results: List[FeatureResponse]
    found_count: int
    missing_count: int
    total_requested: int


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    redis: str
    offline_store_rows: int
    registry_features: int


class StatsResponse(BaseModel):
    offline_store_rows: int
    registry_features: int
    retraining_runs: int
    timestamp: str


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _build_feature_response(entity_id: str, include_embeddings: bool = True) -> FeatureResponse:
    raw = online_store.read(entity_id)
    ttl = online_store.get_ttl(entity_id)

    if raw is None:
        return FeatureResponse(
            entity_id=entity_id,
            timestamp=None,
            event_type=None,
            feature_version=None,
            ttl_seconds=-2,
            features={},
            found=False,
        )

    features = dict(raw)

    # Strip embedding dims if not requested — reduces payload size significantly
    if not include_embeddings:
        features = {k: v for k, v in features.items() if not k.startswith("emb_")}

    # Pull metadata out of feature dict for top-level fields
    return FeatureResponse(
        entity_id=entity_id,
        timestamp=features.get("timestamp"),
        event_type=features.get("event_type"),
        feature_version=features.get("feature_version", "v1"),
        ttl_seconds=ttl,
        features=features,
        found=True,
    )


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Check that the API and all backing services are healthy."""
    try:
        online_store.client.ping()
        redis_status = "ok"
    except Exception:
        redis_status = "error"

    return HealthResponse(
        status="ok" if redis_status == "ok" else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        redis=redis_status,
        offline_store_rows=offline_store.count(),
        registry_features=registry.count(),
    )


@app.get("/features/{entity_id}", response_model=FeatureResponse, tags=["Features"])
def get_features(
    entity_id: str,
    include_embeddings: bool = Query(default=False, description="Include 384-dim embedding vector"),
):
    """
    Get the latest feature vector for a single entity (user).
    Reads from Redis online store — sub-millisecond latency.
    Returns 404 if entity has no features computed yet.
    """
    response = _build_feature_response(entity_id, include_embeddings)
    if not response.found:
        raise HTTPException(
            status_code=404,
            detail=f"No features found for entity '{entity_id}'. "
                   f"Make sure the stream consumer is running and events are flowing."
        )
    return response


@app.post("/features/batch", response_model=BatchResponse, tags=["Features"])
def get_features_batch(request: BatchRequest):
    """
    Get features for multiple entities in one request.
    Uses Redis pipeline for a single round trip regardless of batch size.
    """
    if len(request.entity_ids) > 500:
        raise HTTPException(status_code=400, detail="Batch size cannot exceed 500 entities.")

    results = []
    for entity_id in request.entity_ids:
        result = _build_feature_response(entity_id, request.include_embeddings)
        results.append(result)

    found = [r for r in results if r.found]
    missing = [r for r in results if not r.found]

    return BatchResponse(
        results=results,
        found_count=len(found),
        missing_count=len(missing),
        total_requested=len(request.entity_ids),
    )


@app.get("/features/{entity_id}/history", tags=["Features"])
def get_feature_history(
    entity_id: str,
    limit: int = Query(default=10, ge=1, le=100),
):
    """
    Get the N most recent feature records for an entity from the offline store.
    Useful for debugging and point-in-time analysis.
    """
    history = offline_store.read_latest(entity_id, limit=limit)
    if not history:
        raise HTTPException(
            status_code=404,
            detail=f"No history found for entity '{entity_id}'."
        )
    # Strip embeddings from history for readability
    cleaned = []
    for record in history:
        cleaned.append({k: v for k, v in record.items() if not k.startswith("emb_")})
    return {"entity_id": entity_id, "count": len(cleaned), "history": cleaned}


@app.get("/schema", tags=["Schema"])
def get_schema(
    limit: int = Query(default=50, ge=1, le=500),
    exclude_embeddings: bool = Query(default=True),
):
    """
    Get the registered feature schema — names, types, versions.
    """
    all_features = registry.get_all()
    if exclude_embeddings:
        all_features = [f for f in all_features if not f["feature_name"].startswith("emb_")]
    return {
        "total_features": registry.count(),
        "shown": len(all_features[:limit]),
        "features": all_features[:limit],
    }


@app.get("/stats", response_model=StatsResponse, tags=["System"])
def get_stats():
    """
    Get store statistics — row counts, registry size, retraining history length.
    """
    retraining_history = offline_store.get_retraining_history()
    return StatsResponse(
        offline_store_rows=offline_store.count(),
        registry_features=registry.count(),
        retraining_runs=len(retraining_history),
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/retraining/history", tags=["Retraining"])
def get_retraining_history():
    """Get full retraining history log."""
    history = offline_store.get_retraining_history()
    return {"count": len(history), "history": history}

@app.get("/model/active", tags=["Model"])
def get_active_model():
    """Get the currently active model version and its metrics."""
    active = model_registry.get_active()
    if not active:
        raise HTTPException(status_code=404, detail="No active model found. Run train_baseline.py first.")
    return active


@app.get("/model/versions", tags=["Model"])
def get_model_versions():
    """List all model versions registered in MLflow."""
    runs = model_registry.get_all_runs()
    return {"count": len(runs), "versions": runs}

@app.get("/drift/latest", tags=["Drift"])
def get_latest_drift():
    """Get the most recent drift check report."""
    report = detector.get_latest()
    if not report:
        raise HTTPException(
            status_code=404,
            detail="No drift reports found. Start the drift scheduler first."
        )
    return report


@app.get("/drift/history", tags=["Drift"])
def get_drift_history(limit: int = Query(default=20, ge=1, le=200)):
    """Get recent drift check history — summary rows only."""
    history = detector.get_history(limit=limit)
    return {"count": len(history), "history": history}


@app.post("/drift/check", tags=["Drift"])
def trigger_drift_check(window_minutes: int = Query(default=60, ge=5, le=1440)):
    """
    Manually trigger a drift check on demand.
    Useful for testing and the dashboard trigger button.
    """
    report = detector.run_check(window_minutes=window_minutes)
    return report


@app.get("/drift/snapshot", tags=["Drift"])
def get_snapshot_info():
    """Get metadata about the current reference distribution snapshot."""
    if not snapshot.is_loaded():
        raise HTTPException(
            status_code=404,
            detail="No snapshot loaded. Run scripts/train_baseline.py first."
        )
    features = snapshot.feature_names()
    sample = snapshot.get_feature_stats(features[0]) if features else {}
    return {
        "loaded_at": snapshot.loaded_at,
        "n_features": len(features),
        "feature_names": features,
        "sample_feature": {"name": features[0], "stats": sample} if features else {},
    }

@app.get("/", tags=["System"])
def root():
    return {
        "name": "Streaming Feature Store API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": [
            "GET  /health",
            "GET  /stats",
            "GET  /schema",
            "GET  /features/{entity_id}",
            "GET  /features/{entity_id}/history",
            "POST /features/batch",
            "GET  /retraining/history",
        ]
    }