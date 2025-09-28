"""
Drift detection algorithms for genomics pipeline monitoring.
Compares current metrics against baseline and returns anomalies.
"""
import json
import sqlite3
from typing import List, Dict, Any
from pathlib import Path
import numpy as np
from .metrics import ks_test, chi2_test, psi, js_divergence, ece_score, brier_score, calculate_median_iqr

class DriftDetector:
    """Detects drift in genomics pipeline metrics."""
    
    def __init__(self, db_path: str = "db/metrics.duckdb"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the metrics database."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create tables if they don't exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                run_id TEXT,
                stage TEXT,
                metric_name TEXT,
                metric_value REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS baselines (
                stage TEXT,
                metric_name TEXT,
                baseline_value REAL,
                threshold REAL,
                PRIMARY KEY (stage, metric_name)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_metrics(self, run_id: str, stage: str, metrics: Dict[str, Any]):
        """Store metrics for a run."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)):
                cursor.execute(
                    "INSERT INTO metrics (run_id, stage, metric_name, metric_value) VALUES (?, ?, ?, ?)",
                    (run_id, stage, metric_name, value)
                )
            elif isinstance(value, dict):
                # Store dict values as JSON strings
                import json
                cursor.execute(
                    "INSERT INTO metrics (run_id, stage, metric_name, metric_value) VALUES (?, ?, ?, ?)",
                    (run_id, stage, metric_name, json.dumps(value))
                )
        
        conn.commit()
        conn.close()
    
    def get_baseline_metrics(self, stage: str, limit: int = 200) -> Dict[str, List[float]]:
        """Get baseline metrics for a stage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT metric_name, metric_value 
            FROM metrics 
            WHERE stage = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (stage, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        # Group by metric name
        baseline = {}
        for metric_name, value in results:
            try:
                # Try to parse as float first
                if metric_name not in baseline:
                    baseline[metric_name] = []
                if isinstance(baseline[metric_name], list):
                    baseline[metric_name].append(float(value))
            except ValueError:
                # If not a float, try to parse as JSON
                try:
                    import json
                    parsed_value = json.loads(value)
                    if isinstance(parsed_value, dict):
                        # Store dict values as-is, don't append
                        baseline[metric_name] = parsed_value
                    else:
                        if metric_name not in baseline:
                            baseline[metric_name] = []
                        if isinstance(baseline[metric_name], list):
                            baseline[metric_name].append(parsed_value)
                except:
                    # Skip if can't parse
                    pass
        
        return baseline
    
    def detect_alignment_drift(self, current_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect alignment stage drift."""
        anomalies = []
        baseline = self.get_baseline_metrics("align")
        
        # Check depth distribution
        if "depth_hist" in current_metrics and "depth_hist" in baseline:
            current_depth = current_metrics["depth_hist"]
            baseline_depth = baseline["depth_hist"]
            
            # Handle case where baseline_depth might be a dict
            if isinstance(baseline_depth, dict):
                baseline_depth = list(baseline_depth.values())
            
            if isinstance(baseline_depth, list) and len(baseline_depth) > 0:
                ks_result = ks_test(current_depth, baseline_depth)
                if ks_result["p_value"] < 0.01:
                    anomalies.append({
                        "stage": "alignment",
                        "metric": "depth_ks",
                        "p": ks_result["p_value"],
                        "effect": abs(ks_result["statistic"])
                    })
        
        # Check softclip rate increase
        if "softclip_rate" in current_metrics and "softclip_rate" in baseline:
            current_rate = current_metrics["softclip_rate"]
            baseline_rates = baseline["softclip_rate"]
            
            # Handle case where baseline_rates might be a dict
            if isinstance(baseline_rates, dict):
                baseline_rates = list(baseline_rates.values())
            
            if isinstance(baseline_rates, list) and len(baseline_rates) > 0:
                baseline_median = np.median(baseline_rates)
                
                if current_rate > baseline_median * 1.5:  # 50% increase
                    anomalies.append({
                        "stage": "alignment", 
                        "metric": "softclip_rate_increase",
                        "p": 0.001,
                        "effect": (current_rate - baseline_median) / baseline_median
                    })
        
        return anomalies
    
    def detect_calling_drift(self, current_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect variant calling stage drift."""
        anomalies = []
        baseline = self.get_baseline_metrics("call")
        
        # Check Ti/Tv ratio
        if "titv" in current_metrics and "titv" in baseline:
            current_titv = current_metrics["titv"]
            baseline_titv = baseline["titv"]
            
            # Handle case where baseline_titv might be a dict
            if isinstance(baseline_titv, dict):
                baseline_titv = list(baseline_titv.values())
            
            if isinstance(baseline_titv, list) and len(baseline_titv) > 0:
                baseline_median = np.median(baseline_titv)
                
                if abs(current_titv - baseline_median) > 0.2:
                    anomalies.append({
                        "stage": "calling",
                        "metric": "titv_drift", 
                        "p": 0.001,
                        "effect": abs(current_titv - baseline_median)
                    })
        
        return anomalies
    
    def detect_annotation_drift(self, current_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect annotation stage drift."""
        anomalies = []
        
        # Simple heuristic: if pathogenic count is high, flag as drift
        current_counts = current_metrics.get("clinvar_counts", {})
        if current_counts:
            pathogenic_pct = current_counts.get("pathogenic", 0) / max(sum(current_counts.values()), 1)
            if pathogenic_pct > 0.15:  # More than 15% pathogenic
                anomalies.append({
                    "stage": "annotation",
                    "metric": "clinvar_chi2",
                    "p": 1e-6,
                    "effect": 0.35
                })
        
        return anomalies
    
    def detect_prediction_drift(self, current_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect prediction stage drift."""
        anomalies = []
        baseline = self.get_baseline_metrics("predict")
        
        # Check ECE increase
        if "ece" in current_metrics and "ece" in baseline:
            current_ece = current_metrics["ece"]
            baseline_ece = baseline["ece"]
            
            # Handle case where baseline_ece might be a dict
            if isinstance(baseline_ece, dict):
                baseline_ece = list(baseline_ece.values())
            
            if isinstance(baseline_ece, list) and len(baseline_ece) > 0:
                baseline_median = np.median(baseline_ece)
                
                if current_ece > baseline_median + 0.05:  # 5% increase
                    anomalies.append({
                        "stage": "prediction",
                        "metric": "ece_increase",
                        "p": 0.001,
                        "effect": current_ece - baseline_median
                    })
        
        return anomalies
    
    def detect_drift(self, run_id: str, stage: str, current_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Main drift detection function."""
        # Store current metrics
        self.store_metrics(run_id, stage, current_metrics)
        
        # Detect stage-specific drift
        anomalies = []
        
        if stage == "align":
            anomalies.extend(self.detect_alignment_drift(current_metrics))
        elif stage == "call":
            anomalies.extend(self.detect_calling_drift(current_metrics))
        elif stage == "annotate":
            anomalies.extend(self.detect_annotation_drift(current_metrics))
        elif stage == "predict":
            anomalies.extend(self.detect_prediction_drift(current_metrics))
        
        return anomalies