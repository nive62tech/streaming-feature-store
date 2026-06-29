import pytest
from fastapi.testclient import TestClient
from feature_store.serving.api import app

client = TestClient(app)


class TestHealthEndpoint:

    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_contains_required_fields(self):
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "redis" in data
        assert "offline_store_rows" in data
        assert "registry_features" in data
        assert "timestamp" in data


class TestRootEndpoint:

    def test_root_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_contains_endpoints(self):
        response = client.get("/")
        data = response.json()
        assert "endpoints" in data
        assert len(data["endpoints"]) > 0


class TestStatsEndpoint:

    def test_stats_returns_200(self):
        response = client.get("/stats")
        assert response.status_code == 200

    def test_stats_contains_counts(self):
        response = client.get("/stats")
        data = response.json()
        assert "offline_store_rows" in data
        assert "registry_features" in data
        assert "retraining_runs" in data


class TestSchemaEndpoint:

    def test_schema_returns_200(self):
        response = client.get("/schema")
        assert response.status_code == 200

    def test_schema_excludes_embeddings_by_default(self):
        response = client.get("/schema?exclude_embeddings=true")
        data = response.json()
        feature_names = [f["feature_name"] for f in data["features"]]
        emb_features = [n for n in feature_names if n.startswith("emb_")]
        assert len(emb_features) == 0

    def test_schema_limit_respected(self):
        response = client.get("/schema?limit=5&exclude_embeddings=true")
        data = response.json()
        assert len(data["features"]) <= 5


class TestFeaturesEndpoint:

    def test_missing_entity_returns_404(self):
        response = client.get("/features/nonexistent_user_xyz_999")
        assert response.status_code == 404

    def test_batch_empty_list(self):
        response = client.post(
            "/features/batch",
            json={"entity_ids": [], "include_embeddings": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_requested"] == 0

    def test_batch_missing_entities(self):
        response = client.post(
            "/features/batch",
            json={"entity_ids": ["ghost_user_aaa", "ghost_user_bbb"], "include_embeddings": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["missing_count"] == 2
        assert data["found_count"] == 0

    def test_batch_size_limit(self):
        entity_ids = [f"user_{i}" for i in range(501)]
        response = client.post(
            "/features/batch",
            json={"entity_ids": entity_ids, "include_embeddings": False}
        )
        assert response.status_code == 400


class TestDriftEndpoints:

    def test_drift_snapshot_returns_200_or_404(self):
        response = client.get("/drift/snapshot")
        assert response.status_code in [200, 404]

    def test_drift_history_returns_200(self):
        response = client.get("/drift/history")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "count" in data

    def test_drift_check_trigger_returns_200(self):
        response = client.post("/drift/check?window_minutes=60")
        assert response.status_code == 200

    def test_drift_latest_returns_200_or_404(self):
        response = client.get("/drift/latest")
        assert response.status_code in [200, 404]


class TestModelEndpoints:

    def test_model_versions_returns_200(self):
        response = client.get("/model/versions")
        assert response.status_code == 200
        data = response.json()
        assert "versions" in data

    def test_active_model_returns_200_or_404(self):
        response = client.get("/model/active")
        assert response.status_code in [200, 404]


class TestRetrainingEndpoints:

    def test_retraining_history_returns_200(self):
        response = client.get("/retraining/history")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data

    def test_retraining_status_returns_200(self):
        response = client.get("/retraining/status")
        assert response.status_code == 200
        data = response.json()
        assert "retraining_in_progress" in data