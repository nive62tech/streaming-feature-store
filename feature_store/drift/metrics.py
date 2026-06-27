import numpy as np
import logging
from scipy import stats
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

# PSI severity thresholds — industry standard
PSI_NO_DRIFT = 0.1        # PSI < 0.1  — no significant drift
PSI_MODERATE = 0.2        # PSI < 0.2  — moderate drift, monitor closely
PSI_SEVERE = 0.2          # PSI >= 0.2 — severe drift, trigger retraining

# KS test p-value threshold
KS_ALPHA = 0.05           # p < 0.05 means distributions are significantly different


def compute_psi(
    reference: np.ndarray,
    current: np.ndarray,
    bins: int = 10,
    epsilon: float = 1e-6,
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute Population Stability Index between reference and current distributions.

    PSI = sum((current_pct - reference_pct) * ln(current_pct / reference_pct))

    Interpretation:
    - PSI < 0.1  : No significant drift
    - PSI < 0.2  : Moderate drift — monitor
    - PSI >= 0.2 : Severe drift — retrain

    Args:
        reference: 1D array of feature values from training distribution
        current:   1D array of feature values from live distribution
        bins:      Number of histogram bins
        epsilon:   Small value to avoid log(0)

    Returns:
        psi_value: scalar PSI score
        details:   dict with per-bin breakdown
    """
    reference = np.array(reference, dtype=float)
    current = np.array(current, dtype=float)

    # Use reference distribution to define bin edges
    min_val = min(reference.min(), current.min())
    max_val = max(reference.max(), current.max())

    if max_val == min_val:
        return 0.0, {"bins": bins, "note": "constant feature — no drift possible"}

    bin_edges = np.linspace(min_val, max_val, bins + 1)

    ref_counts, _ = np.histogram(reference, bins=bin_edges)
    cur_counts, _ = np.histogram(current, bins=bin_edges)

    # Convert to proportions
    ref_pct = ref_counts / (len(reference) + epsilon)
    cur_pct = cur_counts / (len(current) + epsilon)

    # Add epsilon to avoid division by zero and log(0)
    ref_pct = np.where(ref_pct == 0, epsilon, ref_pct)
    cur_pct = np.where(cur_pct == 0, epsilon, cur_pct)

    # PSI formula
    psi_bins = (cur_pct - ref_pct) * np.log(cur_pct / ref_pct)
    psi_value = float(np.sum(psi_bins))

    details = {
        "bins": bins,
        "bin_edges": bin_edges.tolist(),
        "ref_pct": ref_pct.tolist(),
        "cur_pct": cur_pct.tolist(),
        "psi_per_bin": psi_bins.tolist(),
    }

    return psi_value, details


def compute_ks(
    reference: np.ndarray,
    current: np.ndarray,
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Compute Kolmogorov-Smirnov test between reference and current distributions.

    The KS statistic measures the maximum absolute difference between
    the empirical CDFs of two samples.

    Args:
        reference: 1D array from training distribution
        current:   1D array from live distribution

    Returns:
        ks_statistic: float — max CDF difference (0 to 1)
        p_value:      float — probability of seeing this difference by chance
        details:      dict with test metadata
    """
    reference = np.array(reference, dtype=float)
    current = np.array(current, dtype=float)

    ks_stat, p_value = stats.ks_2samp(reference, current)

    details = {
        "ks_statistic": float(ks_stat),
        "p_value": float(p_value),
        "significant": p_value < KS_ALPHA,
        "ref_mean": float(reference.mean()),
        "cur_mean": float(current.mean()),
        "ref_std": float(reference.std()),
        "cur_std": float(current.std()),
        "ref_n": len(reference),
        "cur_n": len(current),
    }

    return float(ks_stat), float(p_value), details


def interpret_psi(psi: float) -> str:
    if psi < 0.1:
        return "no_drift"
    elif psi < 0.2:
        return "moderate_drift"
    else:
        return "severe_drift"


def compute_feature_drift(
    feature_name: str,
    reference_values: np.ndarray,
    current_values: np.ndarray,
) -> Dict[str, Any]:
    """
    Run both PSI and KS tests for a single feature.
    Returns a unified result dict.
    """
    if len(current_values) < 30:
        return {
            "feature": feature_name,
            "skipped": True,
            "reason": f"Too few samples: {len(current_values)} (need >= 30)",
        }

    psi, psi_details = compute_psi(reference_values, current_values)
    ks_stat, p_value, ks_details = compute_ks(reference_values, current_values)

    drift_label = interpret_psi(psi)
    ks_drift = p_value < KS_ALPHA

    return {
        "feature": feature_name,
        "skipped": False,
        "psi": round(psi, 6),
        "psi_label": drift_label,
        "ks_statistic": round(ks_stat, 6),
        "ks_p_value": round(p_value, 6),
        "ks_drift_detected": ks_drift,
        "drift_detected": drift_label in ("moderate_drift", "severe_drift") or ks_drift,
        "current_mean": round(float(current_values.mean()), 6),
        "current_std": round(float(current_values.std()), 6),
        "ref_mean": round(psi_details.get("ref_pct", [0])[0], 6) if not psi_details.get("note") else 0.0,
    }