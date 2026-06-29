import logging
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
from feature_store.config import settings
from feature_store.retraining.trainer import FeatureTrainer, TRAINING_FEATURES

logger = logging.getLogger(__name__)


class RetrainingTrigger:
    """
    Watches drift reports and triggers retraining when thresholds are exceeded.

    Flow:
    1. Drift report arrives with trigger_retraining=True
    2. Pull fresh features from offline store
    3. Train new model on fresh data
    4. Validate new model against accuracy threshold
    5. Hot-swap if validation passes — zero downtime
    6. Update reference snapshot with new distribution
    7. Log retraining event to SQLite
    """

    def __init__(self):
        self.psi_threshold = settings.drift.PSI_THRESHOLD
        self.min_samples = settings.retraining.MIN_SAMPLES
        self.accuracy_threshold = settings.retraining.ACCURACY_THRESHOLD
        self._retraining_in_progress = False
        logger.info(
            f"RetrainingTrigger initialized — "
            f"min_samples={self.min_samples}, "
            f"accuracy_threshold={self.accuracy_threshold}"
        )

    def should_retrain(self, drift_report: Dict[str, Any]) -> tuple[bool, str]:
        """
        Decide whether to retrain based on drift report.
        Returns (should_retrain, reason).
        """
        if self._retraining_in_progress:
            return False, "Retraining already in progress — skipping."

        if not drift_report.get("trigger_retraining"):
            return False, "Drift below threshold — no retraining needed."

        n_samples = drift_report.get("n_samples", 0)
        if n_samples < self.min_samples:
            return False, (
                f"Insufficient samples: {n_samples} < {self.min_samples}. "
                f"Collect more data before retraining."
            )

        max_psi = drift_report.get("max_psi", 0.0)
        return True, (
            f"Drift threshold exceeded: max_psi={max_psi:.4f} >= {self.psi_threshold}. "
            f"Samples available: {n_samples}."
        )

    def _load_training_data(self) -> pd.DataFrame:
        """Pull all available feature records from offline store."""
        from feature_store.storage.offline_store import offline_store
        records = offline_store.get_training_data()
        if not records:
            raise ValueError("No training data in offline store.")
        df = pd.DataFrame(records)
        logger.info(f"Loaded {len(df)} records for retraining.")
        return df

    def _compute_new_snapshot(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute distribution snapshot from fresh training data."""
        snapshot = {}
        for col in TRAINING_FEATURES:
            if col not in df.columns:
                continue
            values = df[col].fillna(0.0).values.astype(float)
            hist, bin_edges = np.histogram(values, bins=20)
            snapshot[col] = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "p25": float(np.percentile(values, 25)),
                "p50": float(np.percentile(values, 50)),
                "p75": float(np.percentile(values, 75)),
                "histogram": hist.tolist(),
                "bin_edges": bin_edges.tolist(),
                "n_samples": len(values),
            }
        return snapshot

    def run(self, drift_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full retraining pipeline. Called when drift is detected.
        Returns a retraining result dict.
        """
        started_at = datetime.utcnow()
        should, reason = self.should_retrain(drift_report)

        if not should:
            logger.info(f"Retraining skipped: {reason}")
            return {
                "status": "skipped",
                "reason": reason,
                "started_at": started_at.isoformat(),
            }

        logger.info(f"Retraining triggered: {reason}")
        self._retraining_in_progress = True

        try:
            # Step 1 — get current model accuracy as baseline
            from feature_store.retraining.model_registry import model_registry
            current_active = model_registry.get_active()
            accuracy_before = current_active.get("accuracy", 0.0) if current_active else 0.0

            # Step 2 — load fresh training data
            logger.info("Step 1/5 — Loading fresh training data...")
            df = self._load_training_data()

            # Step 3 — train new model
            logger.info("Step 2/5 — Training new model...")
            trainer = FeatureTrainer()
            X, y = trainer.prepare_dataset(df)
            metrics = trainer.train(X, y)
            accuracy_after = metrics["accuracy"]

            # Step 4 — validate via hot-swap check
            logger.info("Step 3/5 — Validating new model...")
            approved = model_registry.hot_swap(
                new_version="pending",
                new_trainer=trainer,
                new_metrics=metrics,
            )

            if not approved:
                result = {
                    "status": "rejected",
                    "reason": (
                        f"New model accuracy {accuracy_after:.4f} did not meet "
                        f"threshold {self.accuracy_threshold} or was worse than current."
                    ),
                    "accuracy_before": accuracy_before,
                    "accuracy_after": accuracy_after,
                    "started_at": started_at.isoformat(),
                    "completed_at": datetime.utcnow().isoformat(),
                }
                self._log_retraining(result, df, reason)
                return result

            # Step 5 — save artifacts and register
            logger.info("Step 4/5 — Saving artifacts and registering...")
            version = f"v_retrain_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            artifact_paths = trainer.save_artifacts(version)
            run_id = model_registry.register(
                trainer=trainer,
                metrics=metrics,
                artifact_paths=artifact_paths,
                version=version,
                tags={
                    "trigger": "drift_detection",
                    "max_psi": str(drift_report.get("max_psi", 0.0)),
                    "n_features_drifted": str(drift_report.get("n_features_drifted", 0)),
                },
            )

            # Step 6 — hot-swap active model pointer
            model_registry.set_active(version, run_id, metrics)
            logger.info(f"Hot-swap complete — active model is now {version}")

            # Step 7 — update reference snapshot with new distribution
            logger.info("Step 5/5 — Updating reference snapshot...")
            new_snapshot = self._compute_new_snapshot(df)
            from feature_store.drift.snapshot import snapshot as dist_snapshot
            dist_snapshot.update(new_snapshot)

            completed_at = datetime.utcnow()
            duration_seconds = (completed_at - started_at).total_seconds()

            result = {
                "status": "success",
                "version": version,
                "run_id": run_id,
                "accuracy_before": accuracy_before,
                "accuracy_after": accuracy_after,
                "accuracy_delta": round(accuracy_after - accuracy_before, 4),
                "n_samples": len(df),
                "trigger_reason": reason,
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "duration_seconds": round(duration_seconds, 2),
            }

            self._log_retraining(result, df, reason)
            logger.info(
                f"Retraining complete — "
                f"version={version}, "
                f"accuracy={accuracy_after:.4f} "
                f"(delta={result['accuracy_delta']:+.4f}), "
                f"duration={duration_seconds:.1f}s"
            )
            return result

        except Exception as e:
            logger.error(f"Retraining failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "started_at": started_at.isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
            }
        finally:
            self._retraining_in_progress = False

    def _log_retraining(
        self,
        result: Dict[str, Any],
        df: pd.DataFrame,
        reason: str,
    ):
        """Log retraining event to SQLite."""
        try:
            from feature_store.storage.offline_store import offline_store
            offline_store.log_retraining(
                reason=reason,
                samples=len(df),
                acc_before=result.get("accuracy_before", 0.0),
                acc_after=result.get("accuracy_after", 0.0),
                model_version=result.get("version", "unknown"),
                status=result.get("status", "unknown"),
            )
        except Exception as e:
            logger.error(f"Failed to log retraining event: {e}")

    @property
    def is_busy(self) -> bool:
        return self._retraining_in_progress


# Global singleton
trigger = RetrainingTrigger()