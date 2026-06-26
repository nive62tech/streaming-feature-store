import os
from dotenv import load_dotenv

load_dotenv()

class KafkaConfig:
    BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    TOPIC_RAW_EVENTS: str = os.getenv("KAFKA_TOPIC_RAW_EVENTS", "raw-events")
    TOPIC_FEATURES: str = os.getenv("KAFKA_TOPIC_FEATURES", "computed-features")
    CONSUMER_GROUP: str = os.getenv("KAFKA_CONSUMER_GROUP", "feature-store-group")

class RedisConfig:
    HOST: str = os.getenv("REDIS_HOST", "localhost")
    PORT: int = int(os.getenv("REDIS_PORT", 6379))
    DB: int = int(os.getenv("REDIS_DB", 0))
    TTL_SECONDS: int = int(os.getenv("REDIS_TTL_SECONDS", 3600))

class OfflineStoreConfig:
    DB_PATH: str = os.getenv("OFFLINE_STORE_DB_PATH", "data/offline_store.db")

class MLflowConfig:
    TRACKING_URI: str = os.getenv("MLFLOW_TRACKING_URI", "./mlruns")

class APIConfig:
    HOST: str = os.getenv("API_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("API_PORT", 8000))

class DriftConfig:
    CHECK_INTERVAL_MINUTES: int = int(os.getenv("DRIFT_CHECK_INTERVAL_MINUTES", 5))
    PSI_THRESHOLD: float = float(os.getenv("DRIFT_PSI_THRESHOLD", 0.2))
    KS_THRESHOLD: float = float(os.getenv("DRIFT_KS_THRESHOLD", 0.05))

class RetrainingConfig:
    MIN_SAMPLES: int = int(os.getenv("MIN_SAMPLES_FOR_RETRAINING", 1000))
    ACCURACY_THRESHOLD: float = float(os.getenv("MODEL_VALIDATION_ACCURACY_THRESHOLD", 0.75))

class Settings:
    kafka = KafkaConfig()
    redis = RedisConfig()
    offline_store = OfflineStoreConfig()
    mlflow = MLflowConfig()
    api = APIConfig()
    drift = DriftConfig()
    retraining = RetrainingConfig()

settings = Settings()
