"""
Configuration settings for GIA system.
Contains thresholds, weights, and system parameters.
"""
from typing import Dict, Any

class Config:
    """Configuration class for GIA system."""
    
    def __init__(self):
        # Drift detection thresholds
        self.thresholds = {
            "alignment": {
                "depth_ks_p": 0.01,
                "depth_median_delta": 0.5,
                "psi_af": 0.2,
                "softclip_rate_increase": 0.5
            },
            "calling": {
                "titv_delta": 0.2,
                "qual_median_delta": 0.5,
                "recall_delta": 0.05
            },
            "annotation": {
                "clinvar_chi2_p": 1e-4,
                "consequence_js": 0.1
            },
            "prediction": {
                "psi_score": 0.2,
                "ece_delta": 0.05,
                "threshold_crossers_delta": 0.05
            },
            "instability": {
                "variant_flip_rate": 0.02
            }
        }
        
        # Hypothesis ranking weights
        self.hypothesis_weights = {
            "version_change_prior": 0.8,
            "anomaly_likelihood": 0.6,
            "effect_size_boost": 0.5,
            "p_value_boost": 0.3
        }
        
        # Probe priorities
        self.probe_priorities = [
            "reannotate",
            "caller_version", 
            "realign_locus",
            "downsample_noise",
            "schema_normalize"
        ]
        
        # Convergence criteria
        self.convergence = {
            "min_explains_pct": 0.8,
            "min_significance_p": 1e-4,
            "max_probes": 5
        }
        
        # System parameters
        self.system = {
            "max_probe_time": 120,  # seconds
            "baseline_window": 200,
            "microcohort_size": 20,
            "simulation_seed": 42
        }
    
    def get_threshold(self, stage: str, metric: str) -> float:
        """Get threshold for a specific metric."""
        return self.thresholds.get(stage, {}).get(metric, 0.01)
    
    def get_weight(self, weight_type: str) -> float:
        """Get weight for hypothesis ranking."""
        return self.hypothesis_weights.get(weight_type, 0.5)
    
    def get_probe_priority(self, probe_type: str) -> int:
        """Get priority order for probe type."""
        try:
            return self.probe_priorities.index(probe_type)
        except ValueError:
            return len(self.probe_priorities)
    
    def is_converged(self, explains_pct: float, p_value: float) -> bool:
        """Check if investigation has converged."""
        return (explains_pct >= self.convergence["min_explains_pct"] and 
                p_value <= self.convergence["min_significance_p"])