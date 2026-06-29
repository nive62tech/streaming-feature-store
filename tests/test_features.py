import pytest
import uuid
from datetime import datetime
from feature_store.computation.windowed_aggregations import WindowedAggregator
from feature_store.computation.feature_pipeline import FeaturePipeline
from feature_store.ingestion.schemas import RawEvent


def make_event(event_type="click", price=None, quantity=None) -> dict:
    return RawEvent(
        event_type=event_type,
        user_id="test_user_0001",
        item_id="item_0001",
        category="electronics",
        price=price,
        quantity=quantity,
        session_id="sess_test_001",
        platform="web",
        region="us-east",
    ).to_dict()


class TestWindowedAggregator:

    def test_add_event_and_count(self):
        agg = WindowedAggregator()
        event = make_event()
        agg.add_event(event)
        features = agg.compute_features("test_user_0001")
        assert features["event_count_1min"] >= 1
        assert features["event_count_5min"] >= 1
        assert features["event_count_1hr"] >= 1

    def test_purchase_price_aggregation(self):
        agg = WindowedAggregator()
        for _ in range(3):
            agg.add_event(make_event(event_type="purchase", price=100.0))
        features = agg.compute_features("test_user_0001")
        assert features["purchase_count_1min"] == 3
        assert features["avg_price_1min"] == pytest.approx(100.0, abs=0.01)
        assert features["total_spend_1min"] == pytest.approx(300.0, abs=0.01)
        assert features["max_price_1min"] == pytest.approx(100.0, abs=0.01)

    def test_multiple_users_isolated(self):
        agg = WindowedAggregator()
        e1 = make_event()
        e1["user_id"] = "user_aaa"
        e2 = make_event()
        e2["user_id"] = "user_bbb"
        agg.add_event(e1)
        agg.add_event(e2)
        f1 = agg.compute_features("user_aaa")
        f2 = agg.compute_features("user_bbb")
        assert f1["event_count_1min"] == 1
        assert f2["event_count_1min"] == 1

    def test_unique_items_counted(self):
        agg = WindowedAggregator()
        for i in range(5):
            e = make_event()
            e["item_id"] = f"item_{i:04d}"
            agg.add_event(e)
        features = agg.compute_features("test_user_0001")
        assert features["unique_items_1min"] == 5

    def test_zero_features_for_unknown_user(self):
        agg = WindowedAggregator()
        features = agg.compute_features("nonexistent_user")
        assert features["event_count_1min"] == 0
        assert features["avg_price_1min"] == 0.0


class TestFeaturePipeline:

    def test_pipeline_returns_required_keys(self):
        pipeline = FeaturePipeline()
        event = make_event(event_type="purchase", price=99.99)
        features = pipeline.process(event, skip_embeddings=True)
        required = [
            "entity_id", "event_id", "timestamp",
            "event_type", "feature_version",
            "event_count_1min", "avg_price_5min", "total_spend_1hr",
        ]
        for key in required:
            assert key in features, f"Missing key: {key}"

    def test_pipeline_entity_id_matches_user(self):
        pipeline = FeaturePipeline()
        event = make_event()
        event["user_id"] = "pipeline_test_user"
        features = pipeline.process(event, skip_embeddings=True)
        assert features["entity_id"] == "pipeline_test_user"

    def test_pipeline_skip_embeddings(self):
        pipeline = FeaturePipeline()
        event = make_event()
        features = pipeline.process(event, skip_embeddings=True)
        emb_keys = [k for k in features if k.startswith("emb_")]
        assert len(emb_keys) == 0

    def test_pipeline_feature_version(self):
        pipeline = FeaturePipeline()
        event = make_event()
        features = pipeline.process(event, skip_embeddings=True)
        assert features["feature_version"] == "v1"

    def test_schema_validates_event(self):
        event = RawEvent(
            event_type="purchase",
            user_id="user_schema_test",
            item_id="item_0001",
            category="books",
            price=29.99,
            quantity=2,
            session_id="sess_schema",
            platform="mobile",
            region="eu-west",
        )
        d = event.to_dict()
        assert d["event_type"] == "purchase"
        assert d["price"] == 29.99
        assert d["platform"] == "mobile"

    def test_get_feature_names_count(self):
        pipeline = FeaturePipeline()
        names = pipeline.get_feature_names()
        assert len(names) == 27 + 384