import json
import logging
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, Integer, Index
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from feature_store.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

class FeatureRecord(Base):
    __tablename__ = "feature_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(String(64), nullable=False, index=True)
    event_id = Column(String(64), nullable=False, unique=True)
    event_type = Column(String(32), nullable=False)
    feature_version = Column(String(16), nullable=False, default="v1")
    timestamp = Column(DateTime, nullable=False, index=True)
    features_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_entity_timestamp", "entity_id", "timestamp"),
    )


class RetrainingLog(Base):
    __tablename__ = "retraining_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    trigger_reason = Column(String(128))
    samples_used = Column(Integer)
    accuracy_before = Column(Float)
    accuracy_after = Column(Float)
    model_version = Column(String(64))
    status = Column(String(32), default="pending")


class OfflineFeatureStore:
    """
    SQLite-backed offline feature store.
    Logs every computed feature vector for historical queries and retraining.
    """

    def __init__(self):
        os.makedirs(os.path.dirname(settings.offline_store.DB_PATH), exist_ok=True)
        db_url = f"sqlite:///{settings.offline_store.DB_PATH}"
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"Offline store initialized at {settings.offline_store.DB_PATH}")

    def write(self, features: Dict[str, Any]):
        """Log a computed feature vector to SQLite."""
        session: Session = self.SessionLocal()
        try:
            ts_raw = features.get("timestamp", datetime.utcnow().isoformat())
            ts = datetime.fromisoformat(ts_raw) if isinstance(ts_raw, str) else ts_raw

            record = FeatureRecord(
                entity_id=features["entity_id"],
                event_id=features["event_id"],
                event_type=features.get("event_type", "unknown"),
                feature_version=features.get("feature_version", "v1"),
                timestamp=ts,
                features_json=json.dumps(features),
            )
            session.add(record)
            session.commit()
            logger.debug(f"Logged features for event {features['event_id']} to offline store.")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to write to offline store: {e}")
        finally:
            session.close()

    def read_latest(self, entity_id: str, limit: int = 10) -> List[Dict]:
        """Get the N most recent feature records for an entity."""
        session = self.SessionLocal()
        try:
            records = (
                session.query(FeatureRecord)
                .filter(FeatureRecord.entity_id == entity_id)
                .order_by(FeatureRecord.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [json.loads(r.features_json) for r in records]
        finally:
            session.close()

    def read_range(self, start: datetime, end: datetime, limit: int = 10000) -> List[Dict]:
        """Get all feature records within a time range. Used for retraining."""
        session = self.SessionLocal()
        try:
            records = (
                session.query(FeatureRecord)
                .filter(FeatureRecord.timestamp >= start)
                .filter(FeatureRecord.timestamp <= end)
                .order_by(FeatureRecord.timestamp.asc())
                .limit(limit)
                .all()
            )
            return [json.loads(r.features_json) for r in records]
        finally:
            session.close()

    def count(self) -> int:
        session = self.SessionLocal()
        try:
            return session.query(FeatureRecord).count()
        finally:
            session.close()

    def get_training_data(self, min_samples: int = 1000) -> List[Dict]:
        """Pull all stored features for model training."""
        session = self.SessionLocal()
        try:
            records = (
                session.query(FeatureRecord)
                .order_by(FeatureRecord.timestamp.asc())
                .all()
            )
            data = [json.loads(r.features_json) for r in records]
            logger.info(f"Pulled {len(data)} records for training.")
            return data
        finally:
            session.close()

    def log_retraining(self, reason: str, samples: int, acc_before: float,
                       acc_after: float, model_version: str, status: str = "success"):
        session = self.SessionLocal()
        try:
            log = RetrainingLog(
                trigger_reason=reason,
                samples_used=samples,
                accuracy_before=acc_before,
                accuracy_after=acc_after,
                model_version=model_version,
                status=status,
            )
            session.add(log)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log retraining: {e}")
        finally:
            session.close()

    def get_retraining_history(self) -> List[Dict]:
        session = self.SessionLocal()
        try:
            logs = session.query(RetrainingLog).order_by(RetrainingLog.triggered_at.desc()).all()
            return [
                {
                    "id": l.id,
                    "triggered_at": l.triggered_at.isoformat(),
                    "trigger_reason": l.trigger_reason,
                    "samples_used": l.samples_used,
                    "accuracy_before": l.accuracy_before,
                    "accuracy_after": l.accuracy_after,
                    "model_version": l.model_version,
                    "status": l.status,
                }
                for l in logs
            ]
        finally:
            session.close()


# Global singleton
offline_store = OfflineFeatureStore()