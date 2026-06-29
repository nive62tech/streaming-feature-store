import pytest
from unittest.mock import patch, MagicMock
from feature_store.retraining.trigger import RetrainingTrigger


def make_drift_report(trigger=True, n_samples=500, max_psi=0.35):
    return {
        "trigger_retraining": trigger,
        "max_psi": max_psi,
        "n_samples": n_samples,
        "n_features_drifted": 5,
        "checked_at": "2024-01-01T00:00:00",
    }


class TestRetrainingTrigger:

    def test_should_not_retrain_when_flag_false(self):
        t = RetrainingTrigger()
        report = make_drift_report(trigger=False)
        should, reason = t.should_retrain(report)
        assert should is False
        assert "below threshold" in reason

    def test_should_not_retrain_when_insufficient_samples(self):
        t = RetrainingTrigger()
        report = make_drift_report(trigger=True, n_samples=5)
        should, reason = t.should_retrain(report)
        assert should is False
        assert "Insufficient samples" in reason

    def test_should_retrain_when_conditions_met(self):
        t = RetrainingTrigger()
        report = make_drift_report(trigger=True, n_samples=500, max_psi=0.35)
        should, reason = t.should_retrain(report)
        assert should is True
        assert "exceeded" in reason

    def test_skips_when_already_in_progress(self):
        t = RetrainingTrigger()
        t._retraining_in_progress = True
        report = make_drift_report(trigger=True, n_samples=500)
        should, reason = t.should_retrain(report)
        assert should is False
        assert "in progress" in reason

    def test_is_busy_property(self):
        t = RetrainingTrigger()
        assert t.is_busy is False
        t._retraining_in_progress = True
        assert t.is_busy is True

    def test_run_returns_skipped_when_no_trigger(self):
        t = RetrainingTrigger()
        report = make_drift_report(trigger=False)
        result = t.run(report)
        assert result["status"] == "skipped"

    def test_run_returns_skipped_when_few_samples(self):
        t = RetrainingTrigger()
        report = make_drift_report(trigger=True, n_samples=2)
        result = t.run(report)
        assert result["status"] == "skipped"


class TestModelRegistry:

    def test_get_active_returns_none_or_dict(self):
        from feature_store.retraining.model_registry import model_registry
        result = model_registry.get_active()
        assert result is None or isinstance(result, dict)

    def test_get_all_runs_returns_list(self):
        from feature_store.retraining.model_registry import model_registry
        runs = model_registry.get_all_runs()
        assert isinstance(runs, list)

    def test_hot_swap_rejects_below_threshold(self):
        from feature_store.retraining.model_registry import ModelRegistry
        registry = ModelRegistry()
        mock_trainer = MagicMock()
        result = registry.hot_swap(
            new_version="test_v",
            new_trainer=mock_trainer,
            new_metrics={"accuracy": 0.01},
        )
        assert result is False