#!/usr/bin/env python3
"""
Test drift detection to verify it works correctly.
"""
import sys
import os
sys.path.append('.')

from analysis.detectors import DriftDetector
from analysis.pipeline import annotate
import tempfile

def test_drift_detection():
    """Test drift detection with annotation drift scenario."""
    print("Testing drift detection...")
    
    detector = DriftDetector()
    
    # Create some baseline metrics first
    print("\n1. Creating baseline metrics...")
    baseline_metrics = {
        "clinvar_counts": {"pathogenic": 20, "benign": 80, "vus": 200},
        "consequence_hist": {"missense": 0.4, "synonymous": 0.3, "nonsense": 0.1},
        "transcript_policy_counts": {"canonical": 0.7, "all": 0.3}
    }
    
    detector.store_metrics("baseline_run", "annotate", baseline_metrics)
    print("✓ Baseline metrics stored")
    
    # Create drifted metrics (simulating DB version change)
    print("\n2. Creating drifted metrics...")
    drifted_metrics = {
        "clinvar_counts": {"pathogenic": 50, "benign": 50, "vus": 200},  # 25% pathogenic
        "consequence_hist": {"missense": 0.5, "synonymous": 0.2, "nonsense": 0.1},  # More missense
        "transcript_policy_counts": {"canonical": 0.6, "all": 0.4}  # More non-canonical
    }
    
    # Detect drift
    print("\n3. Detecting drift...")
    anomalies = detector.detect_drift("drifted_run", "annotate", drifted_metrics)
    print(f"✓ Found {len(anomalies)} anomalies")
    
    for anomaly in anomalies:
        print(f"  - {anomaly['stage']}: {anomaly['metric']} (p={anomaly['p']}, effect={anomaly['effect']})")
    
    # Check if we got annotation drift
    annotation_anomalies = [a for a in anomalies if a['stage'] == 'annotation']
    if annotation_anomalies:
        print("✓ Annotation drift detected as expected")
        return True
    else:
        print("✗ No annotation drift detected")
        return False

if __name__ == "__main__":
    success = test_drift_detection()
    if success:
        print("\n🎉 Drift detection acceptance test PASSED")
        exit(0)
    else:
        print("\n❌ Drift detection acceptance test FAILED")
        exit(1)