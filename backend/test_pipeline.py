#!/usr/bin/env python3
"""
Test pipeline functions to verify they work with exact signatures.
"""
import sys
import os
sys.path.append('.')

from analysis.pipeline import align, call_variants, annotate, predict
import tempfile
import shutil

def test_pipeline_functions():
    """Test all pipeline functions with tiny inputs."""
    print("Testing pipeline functions...")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temp directory: {temp_dir}")
        
        # Test align function
        print("\n1. Testing align function...")
        try:
            bam_path, align_metrics = align(
                "data/inputs/sample_001_R1.fastq.gz",
                "data/inputs/sample_001_R2.fastq.gz", 
                "data/refs/grch37/chr21.fa",
                temp_dir
            )
            print(f"✓ align returned: {bam_path}")
            print(f"✓ align metrics keys: {list(align_metrics.keys())}")
            
            # Check required metrics
            required_keys = ["depth_hist", "dup_rate", "softclip_rate", "gc_bias_proxy"]
            for key in required_keys:
                assert key in align_metrics, f"Missing key: {key}"
            print("✓ All required align metrics present")
            
        except Exception as e:
            print(f"✗ align failed: {e}")
            return False
        
        # Test call_variants function
        print("\n2. Testing call_variants function...")
        try:
            vcf_path, call_metrics = call_variants(
                bam_path,
                "data/refs/grch37/chr21.fa",
                "bcftools",
                temp_dir
            )
            print(f"✓ call_variants returned: {vcf_path}")
            print(f"✓ call_variants metrics keys: {list(call_metrics.keys())}")
            
            # Check required metrics
            required_keys = ["titv", "qual_hist", "per_chr_density"]
            for key in required_keys:
                assert key in call_metrics, f"Missing key: {key}"
            print("✓ All required call metrics present")
            
        except Exception as e:
            print(f"✗ call_variants failed: {e}")
            return False
        
        # Test annotate function
        print("\n3. Testing annotate function...")
        try:
            annot_vcf_path, annot_metrics = annotate(
                vcf_path,
                "vep",
                "v101",
                "canonical",
                temp_dir
            )
            print(f"✓ annotate returned: {annot_vcf_path}")
            print(f"✓ annotate metrics keys: {list(annot_metrics.keys())}")
            
            # Check required metrics
            required_keys = ["clinvar_counts", "consequence_hist", "transcript_policy_counts"]
            for key in required_keys:
                assert key in annot_metrics, f"Missing key: {key}"
            print("✓ All required annotate metrics present")
            
        except Exception as e:
            print(f"✗ annotate failed: {e}")
            return False
        
        # Test predict function
        print("\n4. Testing predict function...")
        try:
            predictions, pred_metrics = predict(
                annot_vcf_path,
                "models/pathogenicity_model.pkl",
                {},
                temp_dir
            )
            print(f"✓ predict returned predictions: {type(predictions)}")
            print(f"✓ predict metrics keys: {list(pred_metrics.keys())}")
            
            # Check required metrics
            required_keys = ["score_mean", "score_var", "threshold_crossers_pct", "ece", "brier"]
            for key in required_keys:
                assert key in pred_metrics, f"Missing key: {key}"
            print("✓ All required predict metrics present")
            
        except Exception as e:
            print(f"✗ predict failed: {e}")
            return False
    
    print("\n✅ All pipeline functions passed!")
    return True

if __name__ == "__main__":
    success = test_pipeline_functions()
    if success:
        print("\n🎉 Pipeline acceptance test PASSED")
        exit(0)
    else:
        print("\n❌ Pipeline acceptance test FAILED")
        exit(1)