import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, Integer, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from feature_store.drift.metrics import compute_feature_drift
from feature_store.drift.snapshot import snapshot
from feature_store.retraining.trainer import TRAINING_FEATURES
from feature_store.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


class DriftReport(Base):
    __tablename__ = "drift_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    checked_at = Column(DateTime, default=datetime.utcnow, index=True)
    window_minutes = Column(Integer, default=60)
    n_samples = Column(Integer, default=0)
    n_features_checked = Column(Integer, default=0)
    n_features_drifted = Column(Integer, default=0)
    max_psi = Column(Float, default=0.0)
    avg_psi = Column(Float, default=0.0)
    drift_detected = Column(Boolean, default=False)
    trigger_retraining = Column(Boolean, default=False)
    report_json = Column(Text)


class DriftDetector:
    """
    Compares live feature distributions (from offline store)
    against the training reference snapshot.

    Runs PSI and KS tests per feature.
    Logs results to SQLite drift_reports table.
    Signals retraining when drift exceeds thresholds.
    """

    def __init__(self):
        import os
        os.makedirs("data", exist_ok=True)
        db_url = f"sqlite:///{settings.offline_store.DB_PATH}"
        self.engine = create_engine(
            db_url, connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.psi_threshold = settings.drift.PSI_THRESHOLD
        self.ks_threshold = settings.drift.KS_THRESHOLD
        logger.info(
            f"DriftDetector initialized — "
            f"PSI threshold: {self.psi_threshold}, "
            f"KS threshold: {self.ks_threshold}"
        )

    def _get_live_features(self, window_minutes: int = 60) -> List[Dict]:
        """Pull recent feature records from offline store."""
        from feature_store.storage.offline_store import offline_store
        start = datetime.utcnow() - timedelta(minutes=window_minutes)
        end = datetime.utcnow()
        records = offline_store.read_range(start, end, limit=10000)
        logger.info(
            f"Pulled {len(records)} live feature records "
            f"from last {window_minutes} minutes."
        )
        return records

    def _extract_feature_values(
        self, records: List[Dict], feature_name: str
    ) -> np.ndarray:
        """Extract values for one feature from a list of feature dicts."""
        values = []
        for r in records:
            v = r.get(feature_name)
            if v is not None:
                try:
                    values.append(float(v))
                except (TypeError, ValueError):
                    continue
        return np.array(values, dtype=float)

    def run_check(self, window_minutes: int = 60) -> Dict[str, Any]:
        """
        Run a full drift check across all training features.
        Returns a drift report dict and saves to SQLite.
        """
        checked_at = datetime.utcnow()

        if not snapshot.is_loaded():
            logger.warning("No snapshot loaded. Skipping drift check.")
            return {"error": "No snapshot available."}

        # Get live data
        live_records = self._get_live_features(window_minutes)
        if len(live_records) < 30:
            logger.warning(
                f"Only {len(live_records)} live samples. "
                f"Need at least 30 for drift check."
            )
            return {
                "checked_at": checked_at.isoformat(),
                "n_samples": len(live_records),
                "drift_detected": False,
                "trigger_retraining": False,
                "note": "Insufficient samples for drift check.",
            }

        # Run per-feature drift tests
        feature_results = []
        psi_values = []

        for feature_name in TRAINING_FEATURES:
            ref_values = snapshot.get_reference_values(feature_name)
            if ref_values is None or len(ref_values) == 0:
                continue

            live_values = self._extract_feature_values(live_records, feature_name)
            result = compute_feature_drift(feature_name, ref_values, live_values)
            feature_results.append(result)

            if not result.get("skipped") and "psi" in result:
                psi_values.append(result["psi"])

        # Aggregate results
        drifted = [r for r in feature_results if r.get("drift_detected")]
        n_drifted = len(drifted)
        max_psi = max(psi_values) if psi_values else 0.0
        avg_psi = float(np.mean(psi_values)) if psi_values else 0.0
        drift_detected = n_drifted > 0
        trigger_retraining = max_psi >= self.psi_threshold

        report = {
            "checked_at": checked_at.isoformat(),
            "window_minutes": window_minutes,
            "n_samples": len(live_records),
            "n_features_checked": len(feature_results),
            "n_features_drifted": n_drifted,
            "max_psi": round(max_psi, 6),
            "avg_psi": round(avg_psi, 6),
            "drift_detected": drift_detected,
            "trigger_retraining": trigger_retraining,
            "drifted_features": [r["feature"] for r in drifted],
            "feature_results": feature_results,
        }

        # Save to SQLite
        self._save_report(report)

        logger.info(
            f"Drift check complete — "
            f"samples={len(live_records)}, "
            f"drifted={n_drifted}/{len(feature_results)}, "
            f"max_psi={max_psi:.4f}, "
            f"trigger_retraining={trigger_retraining}"
        )

        return report

    def _save_report(self, report: Dict[str, Any]):
        """Persist drift report to SQLite."""
        session = self.SessionLocal()
        try:
            record = DriftReport(
                checked_at=datetime.fromisoformat(report["checked_at"]),
                window_minutes=report["window_minutes"],
                n_samples=report["n_samples"],
                n_features_checked=report["n_features_checked"],
                n_features_drifted=report["n_features_drifted"],
                max_psi=report["max_psi"],
                avg_psi=report["avg_psi"],
                drift_detected=report["drift_detected"],
                trigger_retraining=report["trigger_retraining"],
                report_json=json.dumps(report),
            )
            session.add(record)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save drift report: {e}")
        finally:
            session.close()

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get recent drift check history from SQLite."""
        session = self.SessionLocal()
        try:
            reports = (
                session.query(DriftReport)
                .order_by(DriftReport.checked_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": r.id,
                    "checked_at": r.checked_at.isoformat(),
                    "n_samples": r.n_samples,
                    "n_features_checked": r.n_features_checked,
                    "n_features_drifted": r.n_features_drifted,
                    "max_psi": r.max_psi,
                    "avg_psi": r.avg_psi,
                    "drift_detected": r.drift_detected,
                    "trigger_retraining": r.trigger_retraining,
                }
                for r in reports
            ]
        finally:
            session.close()

    def get_latest(self) -> Optional[Dict]:
        """Get the most recent drift report."""
        session = self.SessionLocal()
        try:
            report = (
                session.query(DriftReport)
                .order_by(DriftReport.checked_at.desc())
                .first()
            )
            if not report:
                return None
            return json.loads(report.report_json)
        finally:
            session.close()


# Global singleton
detector = DriftDetector()