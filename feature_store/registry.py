import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from feature_store.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

class FeatureDefinition(Base):
    __tablename__ = "feature_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    feature_name = Column(String(128), nullable=False, unique=True)
    feature_type = Column(String(32), nullable=False)  # float, int, str
    version = Column(String(16), nullable=False, default="v1")
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FeatureRegistry:
    """
    Tracks all registered features — names, types, versions, descriptions.
    Backed by the same SQLite DB as the offline store.
    """

    def __init__(self):
        import os
        os.makedirs(os.path.dirname(settings.offline_store.DB_PATH), exist_ok=True)
        db_url = f"sqlite:///{settings.offline_store.DB_PATH}"
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info("Feature registry initialized.")

    def register(self, name: str, feature_type: str, description: str = "", version: str = "v1"):
        session = self.SessionLocal()
        try:
            existing = session.query(FeatureDefinition).filter_by(feature_name=name).first()
            if existing:
                existing.version = version
                existing.description = description
                existing.updated_at = datetime.utcnow()
            else:
                session.add(FeatureDefinition(
                    feature_name=name,
                    feature_type=feature_type,
                    version=version,
                    description=description,
                ))
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to register feature {name}: {e}")
        finally:
            session.close()

    def register_all(self, feature_names: List[str]):
        """Bulk register features from the pipeline's feature name list."""
        for name in feature_names:
            if name.startswith("emb_"):
                ftype = "float"
                desc = f"Embedding dimension {name.split('_')[1]}"
            elif any(x in name for x in ["count", "unique"]):
                ftype = "int"
                desc = f"Windowed count feature: {name}"
            elif any(x in name for x in ["price", "spend"]):
                ftype = "float"
                desc = f"Windowed price feature: {name}"
            else:
                ftype = "str"
                desc = name
            self.register(name, ftype, desc)
        logger.info(f"Registered {len(feature_names)} features in registry.")

    def get_all(self) -> List[Dict]:
        session = self.SessionLocal()
        try:
            defs = session.query(FeatureDefinition).order_by(FeatureDefinition.feature_name).all()
            return [
                {
                    "feature_name": d.feature_name,
                    "feature_type": d.feature_type,
                    "version": d.version,
                    "description": d.description,
                    "created_at": d.created_at.isoformat(),
                }
                for d in defs
            ]
        finally:
            session.close()

    def count(self) -> int:
        session = self.SessionLocal()
        try:
            return session.query(FeatureDefinition).count()
        finally:
            session.close()


# Global singleton
registry = FeatureRegistry()