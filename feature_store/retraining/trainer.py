import os
import json
import logging
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from feature_store.config import settings

logger = logging.getLogger(__name__)

TRAINING_FEATURES = [
    "event_count_1min", "purchase_count_1min", "click_count_1min", "view_count_1min",
    "avg_price_1min", "max_price_1min", "total_spend_1min",
    "unique_items_1min", "unique_categories_1min",
    "event_count_5min", "purchase_count_5min", "click_count_5min", "view_count_5min",
    "avg_price_5min", "max_price_5min", "total_spend_5min",
    "unique_items_5min", "unique_categories_5min",
    "event_count_1hr", "purchase_count_1hr", "click_count_1hr", "view_count_1hr",
    "avg_price_1hr", "max_price_1hr", "total_spend_1hr",
    "unique_items_1hr", "unique_categories_1hr",
]

TARGET_FEATURE = "event_type"
ARTIFACTS_DIR = "models/artifacts"


class FeatureTrainer:
    """
    Trains a GradientBoosting classifier to predict event_type from
    windowed aggregation features. Used as the baseline model and
    for all subsequent retraining runs.
    """

    def __init__(self):
        os.makedirs(ARTIFACTS_DIR, exist_ok=True)
        self.label_encoder = LabelEncoder()
        self.model = None
        self.feature_columns = TRAINING_FEATURES

    def load_features_from_offline_store(self) -> pd.DataFrame:
        """Pull all feature records from SQLite offline store."""
        from feature_store.storage.offline_store import offline_store
        records = offline_store.get_training_data()
        if not records:
            raise ValueError("No records in offline store. Run consumer first.")
        df = pd.DataFrame(records)
        logger.info(f"Loaded {len(df)} records from offline store.")
        return df

    def load_features_from_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Load seed events CSV and compute windowed features only.
        Embeddings are skipped entirely — not needed for training.
        """
        from feature_store.computation.feature_pipeline import pipeline
        logger.info(f"Loading seed events from {csv_path}...")
        events_df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(events_df)} raw events. Computing windowed features only...")

        feature_records = []
        for i, row in events_df.iterrows():
            try:
                event_dict = row.to_dict()
                # Fix NaN values from CSV
                event_dict = {
                    k: (None if pd.isna(v) else v)
                    for k, v in event_dict.items()
                }
                # skip_embeddings=True — no sentence transformer loaded
                features = pipeline.process(event_dict, skip_embeddings=True)
                feature_records.append(features)
            except Exception as e:
                logger.debug(f"Skipped event {i}: {e}")
                continue

            if (i + 1) % 5000 == 0:
                logger.info(f"Processed {i + 1}/{len(events_df)} events...")

        df = pd.DataFrame(feature_records)
        logger.info(f"Feature computation complete. {len(df)} records ready.")
        return df

    def prepare_dataset(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Extract feature matrix X and label vector y from dataframe."""
        missing = [c for c in self.feature_columns if c not in df.columns]
        if missing:
            logger.warning(f"Missing {len(missing)} feature columns. Filling with 0.")
            for col in missing:
                df[col] = 0.0

        X = df[self.feature_columns].fillna(0.0).values.astype(np.float32)
        y_raw = df[TARGET_FEATURE].fillna("unknown").values
        y = self.label_encoder.fit_transform(y_raw)
        logger.info(
            f"Dataset: X={X.shape}, y={y.shape}, "
            f"classes={list(self.label_encoder.classes_)}"
        )
        return X, y

    def train(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train GradientBoosting model and return evaluation metrics."""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        logger.info(
            f"Training on {len(X_train)} samples, evaluating on {len(X_test)}..."
        )

        self.model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            random_state=42,
        )
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(
            y_test, y_pred,
            target_names=self.label_encoder.classes_,
            output_dict=True,
        )

        metrics = {
            "accuracy": round(accuracy, 4),
            "n_train": len(X_train),
            "n_test": len(X_test),
            "classes": list(self.label_encoder.classes_),
            "classification_report": report,
        }
        logger.info(f"Training complete. Accuracy: {accuracy:.4f}")
        return metrics

    def save_artifacts(self, version: str) -> Dict[str, str]:
        """Save model, label encoder, and feature list to disk."""
        version_dir = os.path.join(ARTIFACTS_DIR, version)
        os.makedirs(version_dir, exist_ok=True)

        model_path = os.path.join(version_dir, "model.joblib")
        encoder_path = os.path.join(version_dir, "label_encoder.joblib")
        features_path = os.path.join(version_dir, "feature_columns.json")

        joblib.dump(self.model, model_path)
        joblib.dump(self.label_encoder, encoder_path)
        with open(features_path, "w") as f:
            json.dump(self.feature_columns, f)

        logger.info(f"Artifacts saved to {version_dir}")
        return {
            "model_path": model_path,
            "encoder_path": encoder_path,
            "features_path": features_path,
            "version_dir": version_dir,
        }

    def load_artifacts(self, version: str):
        """Load a saved model version from disk."""
        version_dir = os.path.join(ARTIFACTS_DIR, version)
        self.model = joblib.load(os.path.join(version_dir, "model.joblib"))
        self.label_encoder = joblib.load(
            os.path.join(version_dir, "label_encoder.joblib")
        )
        with open(os.path.join(version_dir, "feature_columns.json")) as f:
            self.feature_columns = json.load(f)
        logger.info(f"Loaded model version {version}")

    def predict(self, features: Dict[str, Any]) -> str:
        """Predict event type for a single feature dict."""
        x = np.array(
            [[features.get(c, 0.0) for c in self.feature_columns]],
            dtype=np.float32,
        )
        pred = self.model.predict(x)
        return self.label_encoder.inverse_transform(pred)[0]