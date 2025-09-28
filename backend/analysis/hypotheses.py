"""
Hypothesis ranking for genomics pipeline drift investigation.
Ranks potential causes based on version changes and anomaly signatures.
"""
from typing import List, Dict, Any
import numpy as np

class HypothesisRanker:
    """Ranks hypotheses based on evidence and priors."""
    
    def __init__(self):
        # Prior weights for different types of changes
        self.priors = {
            "reference_change": 0.8,
            "db_version_change": 0.9,
            "caller_change": 0.7,
            "model_change": 0.6,
            "batch_effect": 0.3
        }
        
        # Likelihood weights for anomaly signatures
        self.likelihoods = {
            "clinvar_chi2": {"annotation_drift": 0.9, "batch_effect": 0.2},
            "per_chr_density": {"reference_drift": 0.8, "batch_effect": 0.3},
            "titv_drift": {"caller_drift": 0.8, "batch_effect": 0.4},
            "softclip_rate": {"mapping_bias": 0.7, "batch_effect": 0.3},
            "ece_increase": {"schema_mismatch": 0.8, "model_drift": 0.6},
            "consequence_js": {"annotation_drift": 0.7, "batch_effect": 0.2}
        }
        
        # Hypothesis definitions
        self.hypotheses = {
            "annotation_drift": {
                "label": "Annotation database drift",
                "signatures": ["clinvar_chi2", "consequence_js"],
                "version_indicators": ["db_version_change"]
            },
            "caller_drift": {
                "label": "Variant caller drift", 
                "signatures": ["titv_drift"],
                "version_indicators": ["caller_change"]
            },
            "reference_drift": {
                "label": "Reference genome drift",
                "signatures": ["per_chr_density"],
                "version_indicators": ["reference_change"]
            },
            "mapping_bias": {
                "label": "Mapping bias",
                "signatures": ["softclip_rate"],
                "version_indicators": []
            },
            "schema_mismatch": {
                "label": "Schema mismatch",
                "signatures": ["ece_increase"],
                "version_indicators": ["model_change"]
            },
            "batch_effect": {
                "label": "Batch effect",
                "signatures": ["clinvar_chi2", "per_chr_density", "titv_drift"],
                "version_indicators": []
            }
        }
    
    def rank_hypotheses(self, kg_delta: Dict[str, Any], anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank hypotheses based on evidence."""
        scores = {}
        
        # Extract version changes from kg_delta
        version_changes = self._extract_version_changes(kg_delta)
        
        # Extract anomaly signatures
        anomaly_signatures = [anomaly["metric"] for anomaly in anomalies]
        
        # Score each hypothesis
        for hyp_id, hyp_data in self.hypotheses.items():
            score = self._calculate_hypothesis_score(
                hyp_id, hyp_data, version_changes, anomaly_signatures, anomalies
            )
            scores[hyp_id] = score
        
        # Sort by score (descending)
        ranked_hypotheses = []
        for hyp_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            ranked_hypotheses.append({
                "id": hyp_id,
                "label": self.hypotheses[hyp_id]["label"],
                "score": round(score, 2)
            })
        
        return ranked_hypotheses
    
    def _extract_version_changes(self, kg_delta: Dict[str, Any]) -> List[str]:
        """Extract version changes from knowledge graph delta."""
        changes = []
        
        if kg_delta.get("reference_changed"):
            changes.append("reference_change")
        if kg_delta.get("db_version_changed"):
            changes.append("db_version_change")
        if kg_delta.get("caller_changed"):
            changes.append("caller_change")
        if kg_delta.get("model_changed"):
            changes.append("model_change")
        
        return changes
    
    def _calculate_hypothesis_score(self, hyp_id: str, hyp_data: Dict[str, Any], 
                                  version_changes: List[str], anomaly_signatures: List[str],
                                  anomalies: List[Dict[str, Any]]) -> float:
        """Calculate score for a hypothesis."""
        score = 0.0
        
        # Prior score based on version changes
        for change in version_changes:
            if change in hyp_data["version_indicators"]:
                score += self.priors.get(change, 0.0)
        
        # Likelihood score based on anomaly signatures
        for signature in anomaly_signatures:
            if signature in hyp_data["signatures"]:
                likelihood = self.likelihoods.get(signature, {}).get(hyp_id, 0.0)
                score += likelihood
        
        # Boost score for strong anomalies
        for anomaly in anomalies:
            if anomaly["metric"] in hyp_data["signatures"]:
                # Boost based on effect size and p-value
                effect_boost = min(anomaly.get("effect", 0.0) * 0.5, 1.0)
                p_boost = max(0.0, -np.log10(anomaly.get("p", 1.0)) * 0.1)
                score += effect_boost + p_boost
        
        return score
    
    def update_hypothesis_confidence(self, hypothesis_id: str, probe_result: Dict[str, Any]) -> float:
        """Update hypothesis confidence based on probe results."""
        base_confidence = 0.5
        
        # Boost confidence based on probe results
        if probe_result.get("explains_pct", 0.0) > 0.8:
            base_confidence += 0.3
        elif probe_result.get("explains_pct", 0.0) > 0.5:
            base_confidence += 0.2
        
        # Boost for significant p-values
        if probe_result.get("p", 1.0) < 1e-4:
            base_confidence += 0.2
        elif probe_result.get("p", 1.0) < 0.01:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)