#!/usr/bin/env python3
"""
Debug simple drift detection.
"""
import sys
import os
sys.path.append('.')

def debug_simple():
    """Debug simple drift detection."""
    print("Debugging simple drift detection...")
    
    # Create drifted metrics (simulating DB version change)
    drifted_metrics = {
        "clinvar_counts": {"pathogenic": 35, "benign": 65, "vus": 200},  # More pathogenic
        "consequence_hist": {"missense": 0.5, "synonymous": 0.2, "nonsense": 0.1},  # More missense
        "transcript_policy_counts": {"canonical": 0.6, "all": 0.4}  # More non-canonical
    }
    
    print(f"Drifted metrics: {drifted_metrics}")
    
    # Test the simple heuristic
    current_counts = drifted_metrics.get("clinvar_counts", {})
    print(f"Current counts: {current_counts}")
    
    if current_counts:
        pathogenic_pct = current_counts.get("pathogenic", 0) / max(sum(current_counts.values()), 1)
        print(f"Pathogenic percentage: {pathogenic_pct}")
        print(f"Threshold check: {pathogenic_pct} > 0.15 = {pathogenic_pct > 0.15}")
        
        if pathogenic_pct > 0.15:  # More than 15% pathogenic
            print("✓ Would detect drift!")
        else:
            print("✗ Would not detect drift")

if __name__ == "__main__":
    debug_simple()