import json
import logging
import redis
from typing import Optional, Dict, Any
from feature_store.config import settings

logger = logging.getLogger(__name__)

class OnlineFeatureStore:
    """
    Redis-backed online feature store.
    Stores latest feature vector per entity (user).
    Keys: features:{entity_id}
    TTL: configurable (default 1hr)
    """

    KEY_PREFIX = "features"
    META_PREFIX = "meta"

    def __init__(self):
        self.client = redis.Redis(
            host=settings.redis.HOST,
            port=settings.redis.PORT,
            db=settings.redis.DB,
            decode_responses=True,
        )
        self.ttl = settings.redis.TTL_SECONDS
        self._verify_connection()

    def _verify_connection(self):
        try:
            self.client.ping()
            logger.info("Online store connected to Redis.")
        except redis.ConnectionError as e:
            logger.error(f"Redis connection failed: {e}")
            raise

    def _key(self, entity_id: str) -> str:
        return f"{self.KEY_PREFIX}:{entity_id}"

    def _meta_key(self, entity_id: str) -> str:
        return f"{self.META_PREFIX}:{entity_id}"

    def write(self, entity_id: str, features: Dict[str, Any]):
        """Write full feature dict for an entity. Overwrites previous."""
        try:
            key = self._key(entity_id)
            # Store numeric and string features separately for efficiency
            serialized = json.dumps(features)
            self.client.set(key, serialized, ex=self.ttl)
            logger.debug(f"Written features for {entity_id} to Redis.")
        except Exception as e:
            logger.error(f"Failed to write features for {entity_id}: {e}")
            raise

    def read(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Read latest feature dict for an entity. Returns None if not found."""
        try:
            key = self._key(entity_id)
            data = self.client.get(key)
            if data is None:
                logger.debug(f"No features found for {entity_id} in Redis.")
                return None
            return json.loads(data)
        except Exception as e:
            logger.error(f"Failed to read features for {entity_id}: {e}")
            return None

    def read_batch(self, entity_ids: list[str]) -> Dict[str, Optional[Dict]]:
        """Read features for multiple entities in one round trip using pipeline."""
        pipe = self.client.pipeline()
        for entity_id in entity_ids:
            pipe.get(self._key(entity_id))
        results = pipe.execute()
        return {
            entity_id: json.loads(data) if data else None
            for entity_id, data in zip(entity_ids, results)
        }

    def delete(self, entity_id: str):
        self.client.delete(self._key(entity_id))

    def exists(self, entity_id: str) -> bool:
        return bool(self.client.exists(self._key(entity_id)))

    def get_ttl(self, entity_id: str) -> int:
        """Returns remaining TTL in seconds. -1 if no expiry. -2 if not found."""
        return self.client.ttl(self._key(entity_id))

    def flush_all(self):
        """Danger: clears all keys. Only for testing."""
        self.client.flushdb()
        logger.warning("Redis DB flushed.")


# Global singleton
online_store = OnlineFeatureStore()