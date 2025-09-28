#!/usr/bin/env python3
"""
Debug drift detection to see what's happening.
"""
import sys
import os
sys.path.append('.')

from analysis.detectors import DriftDetector

def debug_detector():
    """Debug the drift detector."""
    print("Debugging drift detection...")
    
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
    
    # Check what baseline data we have
    baseline = detector.get_baseline_metrics("annotate")
    print(f"Baseline data: {baseline}")
    
    # Create drifted metrics (simulating DB version change)
    print("\n2. Creating drifted metrics...")
    drifted_metrics = {
        "clinvar_counts": {"pathogenic": 35, "benign": 65, "vus": 200},  # More pathogenic
        "consequence_hist": {"missense": 0.5, "synonymous": 0.2, "nonsense": 0.1},  # More missense
        "transcript_policy_counts": {"canonical": 0.6, "all": 0.4}  # More non-canonical
    }
    
    # Test the annotation drift detection directly
    print("\n3. Testing annotation drift detection directly...")
    anomalies = detector.detect_annotation_drift(drifted_metrics)
    print(f"Direct annotation drift detection found {len(anomalies)} anomalies")
    
    for anomaly in anomalies:
        print(f"  - {anomaly}")
    
    # Test the full detect_drift method
    print("\n4. Testing full detect_drift method...")
    all_anomalies = detector.detect_drift("drifted_run", "annotate", drifted_metrics)
    print(f"Full detect_drift found {len(all_anomalies)} anomalies")
    
    for anomaly in all_anomalies:
        print(f"  - {anomaly}")

if __name__ == "__main__":
    debug_detector()