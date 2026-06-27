import pickle
import logging
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

SNAPSHOT_PATH = "data/snapshots/training_distribution.pkl"


class DistributionSnapshot:
    """
    Manages the reference distribution snapshot.
    Loaded once at startup, updated after each successful retraining.
    """

    def __init__(self):
        self._snapshot: Optional[Dict[str, Any]] = None
        self._loaded_at: Optional[datetime] = None
        self.load()

    def load(self):
        """Load snapshot from disk."""
        try:
            with open(SNAPSHOT_PATH, "rb") as f:
                self._snapshot = pickle.load(f)
            self._loaded_at = datetime.utcnow()
            logger.info(
                f"Snapshot loaded: {len(self._snapshot)} features "
                f"from {SNAPSHOT_PATH}"
            )
        except FileNotFoundError:
            logger.warning(
                f"Snapshot not found at {SNAPSHOT_PATH}. "
                f"Run scripts/train_baseline.py first."
            )
            self._snapshot = None

    def update(self, new_snapshot: Dict[str, Any]):
        """Replace the in-memory snapshot and save to disk."""
        self._snapshot = new_snapshot
        self._loaded_at = datetime.utcnow()
        with open(SNAPSHOT_PATH, "wb") as f:
            pickle.dump(new_snapshot, f)
        logger.info(f"Snapshot updated with {len(new_snapshot)} features.")

    def get_reference_values(self, feature_name: str) -> Optional[np.ndarray]:
        """
        Reconstruct reference values from stored histogram for a feature.
        We use bin midpoints weighted by counts as a proxy for the original values.
        """
        if self._snapshot is None or feature_name not in self._snapshot:
            return None

        stats = self._snapshot[feature_name]
        hist = np.array(stats["histogram"])
        edges = np.array(stats["bin_edges"])
        midpoints = (edges[:-1] + edges[1:]) / 2

        # Reconstruct approximate sample by repeating midpoints by count
        values = np.repeat(midpoints, hist.astype(int))
        if len(values) == 0:
            values = np.array([stats["mean"]])
        return values

    def get_feature_stats(self, feature_name: str) -> Optional[Dict[str, Any]]:
        if self._snapshot is None:
            return None
        return self._snapshot.get(feature_name)

    def feature_names(self) -> list:
        if self._snapshot is None:
            return []
        return list(self._snapshot.keys())

    def is_loaded(self) -> bool:
        return self._snapshot is not None

    @property
    def loaded_at(self) -> Optional[str]:
        return self._loaded_at.isoformat() if self._loaded_at else None


# Global singleton
snapshot = DistributionSnapshot()