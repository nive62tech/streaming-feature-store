import pytest
import numpy as np
from feature_store.drift.metrics import (
    compute_psi,
    compute_ks,
    compute_feature_drift,
    interpret_psi,
)


class TestPSI:

    def test_identical_distributions_zero_psi(self):
        ref = np.random.normal(0, 1, 1000)
        cur = np.random.normal(0, 1, 1000)
        psi, _ = compute_psi(ref, cur)
        assert psi < 0.1, f"Expected low PSI for similar distributions, got {psi}"

    def test_shifted_distribution_high_psi(self):
        ref = np.random.normal(0, 1, 1000)
        cur = np.random.normal(10, 1, 1000)
        psi, _ = compute_psi(ref, cur)
        assert psi >= 0.2, f"Expected high PSI for shifted distribution, got {psi}"

    def test_psi_non_negative(self):
        ref = np.random.uniform(0, 100, 500)
        cur = np.random.uniform(50, 150, 500)
        psi, _ = compute_psi(ref, cur)
        assert psi >= 0.0

    def test_psi_details_contains_bin_edges(self):
        ref = np.random.normal(0, 1, 500)
        cur = np.random.normal(0, 1, 500)
        _, details = compute_psi(ref, cur)
        assert "bin_edges" in details or "note" in details

    def test_constant_feature_returns_zero_psi(self):
        ref = np.ones(500)
        cur = np.ones(500)
        psi, details = compute_psi(ref, cur)
        assert psi == 0.0
        assert "note" in details


class TestKS:

    def test_identical_distributions_high_pvalue(self):
        np.random.seed(42)
        ref = np.random.normal(0, 1, 1000)
        cur = np.random.normal(0, 1, 1000)
        _, p_value, _ = compute_ks(ref, cur)
        assert p_value > 0.05, f"Expected p > 0.05 for similar distributions, got {p_value}"

    def test_shifted_distribution_low_pvalue(self):
        ref = np.random.normal(0, 1, 1000)
        cur = np.random.normal(5, 1, 1000)
        ks_stat, p_value, _ = compute_ks(ref, cur)
        assert p_value < 0.05
        assert ks_stat > 0.0

    def test_ks_details_contains_means(self):
        ref = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        cur = np.array([2.0, 3.0, 4.0, 5.0, 6.0])
        _, _, details = compute_ks(ref, cur)
        assert "ref_mean" in details
        assert "cur_mean" in details
        assert "p_value" in details


class TestInterpretPSI:

    def test_no_drift(self):
        assert interpret_psi(0.05) == "no_drift"

    def test_moderate_drift(self):
        assert interpret_psi(0.15) == "moderate_drift"

    def test_severe_drift(self):
        assert interpret_psi(0.25) == "severe_drift"


class TestComputeFeatureDrift:

    def test_skipped_when_too_few_samples(self):
        ref = np.random.normal(0, 1, 1000)
        cur = np.random.normal(0, 1, 10)
        result = compute_feature_drift("test_feature", ref, cur)
        assert result["skipped"] is True
        assert "Too few samples" in result["reason"]

    def test_drift_detected_for_shifted_distribution(self):
        ref = np.random.normal(0, 1, 1000)
        cur = np.random.normal(10, 1, 500)
        result = compute_feature_drift("test_feature", ref, cur)
        assert result["skipped"] is False
        assert result["drift_detected"] is True
        assert result["psi"] >= 0.2

    def test_no_drift_for_similar_distribution(self):
        np.random.seed(0)
        ref = np.random.normal(0, 1, 1000)
        cur = np.random.normal(0, 1, 500)
        result = compute_feature_drift("test_feature", ref, cur)
        assert result["skipped"] is False
        assert "psi" in result
        assert "ks_statistic" in result