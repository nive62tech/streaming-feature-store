import numpy as np
import logging
from datetime import datetime
from typing import Dict, Any
from feature_store.computation.windowed_aggregations import aggregator
from feature_store.computation.embeddings import embedder

logger = logging.getLogger(__name__)

class FeaturePipeline:
    """
    Unified pipeline: raw event -> feature vector.

    Output feature vector contains:
    - 27 windowed aggregation features (9 per window x 3 windows)
    - 384 embedding dimensions
    - Total: 411 features per event
    """

    def process(self, event: dict) -> Dict[str, Any]:
        user_id = event["user_id"]
        event_id = event["event_id"]
        timestamp = event.get("timestamp", datetime.utcnow().isoformat())

        # Step 1 — update window state with this event
        aggregator.add_event(event)

        # Step 2 — compute windowed features for this user
        window_features = aggregator.compute_features(user_id)

        # Step 3 — compute embedding for this event
        embedding = embedder.embed(event)

        # Step 4 — assemble flat feature dict
        feature_dict = {
            "entity_id": user_id,
            "event_id": event_id,
            "timestamp": timestamp,
            "event_type": event["event_type"],
            "feature_version": "v1",
            **window_features,
        }

        # Step 5 — add embedding as indexed keys
        for i, val in enumerate(embedding):
            feature_dict[f"emb_{i}"] = round(float(val), 6)

        logger.debug(f"Processed event {event_id} for user {user_id} — {len(feature_dict)} features")
        return feature_dict

    def get_feature_names(self) -> list[str]:
        window_names = []
        for w in ["1min", "5min", "1hr"]:
            for stat in ["event_count", "purchase_count", "click_count", "view_count",
                         "avg_price", "max_price", "total_spend", "unique_items", "unique_categories"]:
                window_names.append(f"{stat}_{w}")
        emb_names = [f"emb_{i}" for i in range(384)]
        return window_names + emb_names


# Global singleton
pipeline = FeaturePipeline()