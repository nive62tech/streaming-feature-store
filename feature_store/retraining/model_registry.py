import os
import json
import logging
import mlflow
import mlflow.sklearn
from datetime import datetime
from typing import Optional, Dict, Any, List
from feature_store.config import settings

logger = logging.getLogger(__name__)

ACTIVE_MODEL_PATH = "models/artifacts/active_model.json"
MODEL_NAME = "feature-store-event-classifier"


class ModelRegistry:
    """
    Wraps MLflow local tracking for model versioning.
    Maintains an active model pointer for zero-downtime hot-swap.
    """

    def __init__(self):
        mlflow.set_tracking_uri(settings.mlflow.TRACKING_URI)
        mlflow.set_experiment(MODEL_NAME)
        os.makedirs("models/artifacts", exist_ok=True)
        logger.info(f"MLflow tracking at: {settings.mlflow.TRACKING_URI}")

    def register(
        self,
        trainer,
        metrics: Dict[str, Any],
        artifact_paths: Dict[str, str],
        version: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> str:
        """Log a training run to MLflow and return the run_id."""
        with mlflow.start_run(run_name=version) as run:
            # Log scalar metrics
            mlflow.log_metric("accuracy", metrics["accuracy"])
            mlflow.log_metric("n_train", metrics["n_train"])
            mlflow.log_metric("n_test", metrics["n_test"])

            # Log params
            mlflow.log_param("model_type", "GradientBoostingClassifier")
            mlflow.log_param("n_estimators", 100)
            mlflow.log_param("max_depth", 4)
            mlflow.log_param("feature_count", len(trainer.feature_columns))
            mlflow.log_param("version", version)

            # Log tags
            all_tags = {"version": version, "stage": "baseline"}
            if tags:
                all_tags.update(tags)
            mlflow.set_tags(all_tags)

            # Log the sklearn model
            mlflow.sklearn.log_model(trainer.model, artifact_path="model")

            # Log artifact directory
            mlflow.log_artifacts(artifact_paths["version_dir"], artifact_path="artifacts")

            run_id = run.info.run_id
            logger.info(f"Registered model version {version} — run_id: {run_id}")

        return run_id

    def set_active(self, version: str, run_id: str, metrics: Dict[str, Any]):
        """Update the active model pointer file."""
        active = {
            "version": version,
            "run_id": run_id,
            "accuracy": metrics["accuracy"],
            "registered_at": datetime.utcnow().isoformat(),
            "artifact_dir": f"models/artifacts/{version}",
        }
        with open(ACTIVE_MODEL_PATH, "w") as f:
            json.dump(active, f, indent=2)
        logger.info(f"Active model set to version {version} (accuracy={metrics['accuracy']})")

    def get_active(self) -> Optional[Dict[str, Any]]:
        """Read the current active model pointer."""
        if not os.path.exists(ACTIVE_MODEL_PATH):
            return None
        with open(ACTIVE_MODEL_PATH) as f:
            return json.load(f)

    def get_all_runs(self) -> List[Dict[str, Any]]:
        """List all MLflow runs for this experiment."""
        client = mlflow.tracking.MlflowClient()
        experiment = client.get_experiment_by_name(MODEL_NAME)
        if not experiment:
            return []
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["start_time DESC"],
        )
        return [
            {
                "run_id": r.info.run_id,
                "version": r.data.params.get("version", "unknown"),
                "accuracy": r.data.metrics.get("accuracy", 0.0),
                "n_train": r.data.metrics.get("n_train", 0),
                "started_at": datetime.fromtimestamp(
                    r.info.start_time / 1000
                ).isoformat(),
                "status": r.info.status,
            }
            for r in runs
        ]

    def hot_swap(self, new_version: str, new_trainer, new_metrics: Dict[str, Any]) -> bool:
        """
        Validate new model before swapping.
        Only swap if new model meets accuracy threshold.
        Returns True if swap happened.
        """
        threshold = settings.retraining.ACCURACY_THRESHOLD
        new_acc = new_metrics["accuracy"]

        if new_acc < threshold:
            logger.warning(
                f"Hot-swap rejected: accuracy {new_acc:.4f} below threshold {threshold}. "
                f"Keeping current model."
            )
            return False

        current = self.get_active()
        if current:
            current_acc = current.get("accuracy", 0.0)
            if new_acc < current_acc:
                logger.warning(
                    f"Hot-swap rejected: new accuracy {new_acc:.4f} worse than "
                    f"current {current_acc:.4f}."
                )
                return False

        logger.info(f"Hot-swap approved: {new_acc:.4f} >= threshold {threshold}.")
        return True


# Global singleton
model_registry = ModelRegistry()