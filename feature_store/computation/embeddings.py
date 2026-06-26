from sentence_transformers import SentenceTransformer
import numpy as np
import logging

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"

class EventEmbedder:
    """
    Encodes a raw event into a dense vector using a local sentence-transformers model.
    Model: all-MiniLM-L6-v2 (384 dimensions, ~80MB, runs on CPU)
    """

    def __init__(self):
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        self.model = SentenceTransformer(MODEL_NAME)
        self.embedding_dim = 384
        logger.info("Embedding model loaded.")

    def event_to_text(self, event: dict) -> str:
        parts = [
            f"event type is {event.get('event_type', 'unknown')}",
            f"category is {event.get('category', 'unknown')}",
            f"platform is {event.get('platform', 'unknown')}",
            f"region is {event.get('region', 'unknown')}",
        ]
        if event.get("price"):
            parts.append(f"price is {event['price']}")
        return " ".join(parts)

    def embed(self, event: dict) -> np.ndarray:
        text = self.event_to_text(event)
        vector = self.model.encode(text, normalize_embeddings=True)
        return vector

    def embed_batch(self, events: list[dict]) -> np.ndarray:
        texts = [self.event_to_text(e) for e in events]
        return self.model.encode(texts, normalize_embeddings=True, batch_size=32)


# Global singleton
embedder = EventEmbedder()