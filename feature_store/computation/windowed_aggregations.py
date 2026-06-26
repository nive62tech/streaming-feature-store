from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Any
import threading

class WindowedAggregator:
    """
    Maintains an in-memory sliding window of events per user.
    Computes count, price stats, and category distribution
    over 1min, 5min, and 1hr windows.
    """

    WINDOWS = {
        "1min": timedelta(minutes=1),
        "5min": timedelta(minutes=5),
        "1hr": timedelta(hours=1),
    }

    def __init__(self):
        # user_id -> deque of (timestamp, event_dict)
        self._store: Dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def add_event(self, event: dict):
        user_id = event["user_id"]
        ts = datetime.fromisoformat(event["timestamp"]) if isinstance(event["timestamp"], str) else event["timestamp"]
        with self._lock:
            self._store[user_id].append((ts, event))
            self._evict(user_id)

    def _evict(self, user_id: str):
        cutoff = datetime.utcnow() - self.WINDOWS["1hr"]
        dq = self._store[user_id]
        while dq and dq[0][0] < cutoff:
            dq.popleft()

    def _get_window_events(self, user_id: str, window: timedelta) -> list:
        cutoff = datetime.utcnow() - window
        with self._lock:
            return [e for ts, e in self._store[user_id] if ts >= cutoff]

    def compute_features(self, user_id: str) -> Dict[str, Any]:
        features = {}
        for window_name, window_td in self.WINDOWS.items():
            events = self._get_window_events(user_id, window_td)
            n = len(events)
            prices = [e["price"] for e in events if e.get("price") is not None]
            event_type_counts = {}
            for e in events:
                et = e["event_type"]
                event_type_counts[et] = event_type_counts.get(et, 0) + 1

            features[f"event_count_{window_name}"] = n
            features[f"purchase_count_{window_name}"] = event_type_counts.get("purchase", 0)
            features[f"click_count_{window_name}"] = event_type_counts.get("click", 0)
            features[f"view_count_{window_name}"] = event_type_counts.get("view", 0)
            features[f"avg_price_{window_name}"] = round(sum(prices) / len(prices), 4) if prices else 0.0
            features[f"max_price_{window_name}"] = max(prices) if prices else 0.0
            features[f"total_spend_{window_name}"] = round(sum(prices), 4) if prices else 0.0
            features[f"unique_items_{window_name}"] = len(set(e["item_id"] for e in events))
            features[f"unique_categories_{window_name}"] = len(set(e["category"] for e in events))

        return features


# Global singleton — shared across the consumer and pipeline
aggregator = WindowedAggregator()