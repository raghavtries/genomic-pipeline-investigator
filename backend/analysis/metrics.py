"""
Statistical metrics for genomics pipeline monitoring.
All functions use fixed seeds for deterministic results.
"""
import numpy as np
from scipy import stats
from typing import List, Dict, Any
import json

# Set seed for deterministic results
np.random.seed(42)

def ks_test(current: List[float], baseline: List[float]) -> Dict[str, float]:
    """Kolmogorov-Smirnov test between current and baseline distributions."""
    if len(current) == 0 or len(baseline) == 0:
        return {"statistic": 0.0, "p_value": 1.0}
    
    statistic, p_value = stats.ks_2samp(current, baseline)
    return {"statistic": float(statistic), "p_value": float(p_value)}

def chi2_test(current_counts: Dict[str, int], baseline_counts: Dict[str, int]) -> Dict[str, float]:
    """Chi-squared test for categorical data."""
    # Get all categories
    all_cats = set(current_counts.keys()) | set(baseline_counts.keys())
    
    # Create contingency table
    current_vals = [current_counts.get(cat, 0) for cat in all_cats]
    baseline_vals = [baseline_counts.get(cat, 0) for cat in all_cats]
    
    if sum(current_vals) == 0 or sum(baseline_vals) == 0:
        return {"statistic": 0.0, "p_value": 1.0}
    
    # Normalize to proportions
    current_props = np.array(current_vals) / sum(current_vals)
    baseline_props = np.array(baseline_vals) / sum(baseline_vals)
    
    # Chi-squared test
    statistic, p_value = stats.chisquare(current_props, baseline_props)
    return {"statistic": float(statistic), "p_value": float(p_value)}

def psi(current: List[float], baseline: List[float], bins: int = 10) -> float:
    """Population Stability Index between current and baseline distributions."""
    if len(current) == 0 or len(baseline) == 0:
        return 0.0
    
    # Create bins based on baseline
    min_val = min(min(current), min(baseline))
    max_val = max(max(current), max(baseline))
    
    if min_val == max_val:
        return 0.0
    
    bin_edges = np.linspace(min_val, max_val, bins + 1)
    
    # Calculate histograms
    current_hist, _ = np.histogram(current, bins=bin_edges)
    baseline_hist, _ = np.histogram(baseline, bins=bin_edges)
    
    # Normalize to proportions
    current_props = current_hist / (sum(current_hist) + 1e-10)
    baseline_props = baseline_hist / (sum(baseline_hist) + 1e-10)
    
    # Calculate PSI
    psi_val = 0.0
    for i in range(len(current_props)):
        if baseline_props[i] > 0:
            psi_val += (current_props[i] - baseline_props[i]) * np.log(current_props[i] / baseline_props[i])
    
    return float(psi_val)

def js_divergence(current: List[float], baseline: List[float], bins: int = 10) -> float:
    """Jensen-Shannon divergence between current and baseline distributions."""
    if len(current) == 0 or len(baseline) == 0:
        return 0.0
    
    # Create bins
    min_val = min(min(current), min(baseline))
    max_val = max(max(current), max(baseline))
    
    if min_val == max_val:
        return 0.0
    
    bin_edges = np.linspace(min_val, max_val, bins + 1)
    
    # Calculate histograms
    current_hist, _ = np.histogram(current, bins=bin_edges)
    baseline_hist, _ = np.histogram(baseline, bins=bin_edges)
    
    # Normalize to proportions
    current_props = current_hist / (sum(current_hist) + 1e-10)
    baseline_props = baseline_hist / (sum(baseline_hist) + 1e-10)
    
    # Calculate JS divergence
    m = 0.5 * (current_props + baseline_props)
    js_val = 0.5 * stats.entropy(current_props, m) + 0.5 * stats.entropy(baseline_props, m)
    
    return float(js_val)

def ece_score(y_true: List[int], y_pred: List[float], n_bins: int = 10) -> float:
    """Expected Calibration Error for prediction calibration."""
    if len(y_true) == 0 or len(y_pred) == 0:
        return 0.0
    
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Create bins
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]
    
    ece = 0.0
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        in_bin = (y_pred > bin_lower) & (y_pred <= bin_upper)
        prop_in_bin = in_bin.mean()
        
        if prop_in_bin > 0:
            accuracy_in_bin = y_true[in_bin].mean()
            avg_confidence_in_bin = y_pred[in_bin].mean()
            ece += abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
    
    return float(ece)

def brier_score(y_true: List[int], y_pred: List[float]) -> float:
    """Brier score for prediction quality."""
    if len(y_true) == 0 or len(y_pred) == 0:
        return 0.0
    
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    return float(np.mean((y_pred - y_true) ** 2))

def calculate_median_iqr(data: List[float]) -> Dict[str, float]:
    """Calculate median and IQR for a dataset."""
    if len(data) == 0:
        return {"median": 0.0, "iqr": 0.0}
    
    data = np.array(data)
    median = np.median(data)
    q75, q25 = np.percentile(data, [75, 25])
    iqr = q75 - q25
    
    return {"median": float(median), "iqr": float(iqr)}