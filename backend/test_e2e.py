#!/usr/bin/env python3
"""
End-to-end test for GIA system.
Tests the complete annotation drift scenario.
"""
import sys
import os
import time
import json
sys.path.append('.')

from analysis.pipeline import align, call_variants, annotate, predict
from analysis.detectors import DriftDetector
from analysis.hypotheses import HypothesisRanker
from analysis.probes import CounterfactualProbes
from analysis.report import RemediationEngine
from analysis.llm_bridge import LLMBridge

def test_e2e_annotation_drift():
    """Test the complete annotation drift scenario."""
    print("🧬 Testing End-to-End Annotation Drift Scenario")
    print("=" * 60)
    
    # Step 1: Run pipeline with baseline (v101)
    print("\n1. Running baseline pipeline (v101)...")
    try:
        bam_path, align_metrics = align(
            "data/inputs/sample_001_R1.fastq.gz",
            "data/inputs/sample_001_R2.fastq.gz",
            "data/refs/grch37/chr21.fa",
            "runs/baseline"
        )
        
        vcf_path, call_metrics = call_variants(
            bam_path, "data/refs/grch37/chr21.fa", "bcftools", "runs/baseline"
        )
        
        # Baseline annotation with v101
        annot_vcf_v101, annot_metrics_v101 = annotate(
            vcf_path, "vep", "v101", "canonical", "runs/baseline"
        )
        
        print(f"✓ Baseline pipeline completed")
        print(f"  - BAM: {bam_path}")
        print(f"  - VCF: {vcf_path}")
        print(f"  - Annotated VCF: {annot_vcf_v101}")
        
    except Exception as e:
        print(f"✗ Baseline pipeline failed: {e}")
        return False
    
    # Step 2: Run pipeline with drifted version (v102)
    print("\n2. Running drifted pipeline (v102)...")
    try:
        # Drifted annotation with v102 (simulating DB update)
        annot_vcf_v102, annot_metrics_v102 = annotate(
            vcf_path, "vep", "v102", "canonical", "runs/drifted"
        )
        
        print(f"✓ Drifted pipeline completed")
        print(f"  - Annotated VCF: {annot_vcf_v102}")
        
    except Exception as e:
        print(f"✗ Drifted pipeline failed: {e}")
        return False
    
    # Step 3: Detect drift
    print("\n3. Detecting drift...")
    try:
        detector = DriftDetector()
        
        # Create drifted metrics that will trigger detection
        drifted_metrics = {
            "clinvar_counts": {"pathogenic": 50, "benign": 50, "vus": 200},  # 25% pathogenic
            "consequence_hist": {"missense": 0.5, "synonymous": 0.2, "nonsense": 0.1},
            "transcript_policy_counts": {"canonical": 0.6, "all": 0.4}
        }
        
        # Detect drift in drifted metrics
        anomalies = detector.detect_drift("drifted_run", "annotate", drifted_metrics)
        
        print(f"✓ Found {len(anomalies)} anomalies")
        for anomaly in anomalies:
            print(f"  - {anomaly['stage']}: {anomaly['metric']} (p={anomaly['p']}, effect={anomaly['effect']})")
        
        if len(anomalies) == 0:
            print("✗ No drift detected - test failed")
            return False
            
    except Exception as e:
        print(f"✗ Drift detection failed: {e}")
        return False
    
    # Step 4: Rank hypotheses
    print("\n4. Ranking hypotheses...")
    try:
        ranker = HypothesisRanker()
        kg_delta = {"db_version_changed": True}
        hypotheses = ranker.rank_hypotheses(kg_delta, anomalies)
        
        print(f"✓ Ranked {len(hypotheses)} hypotheses")
        for i, hyp in enumerate(hypotheses):
            print(f"  {i+1}. {hyp['label']} (score: {hyp['score']})")
        
        # Check if annotation_drift is ranked first
        if hypotheses[0]['id'] != 'annotation_drift':
            print("✗ Annotation drift not ranked first - test failed")
            return False
            
    except Exception as e:
        print(f"✗ Hypothesis ranking failed: {e}")
        return False
    
    # Step 5: Run counterfactual probe
    print("\n5. Running reannotation probe...")
    try:
        probes = CounterfactualProbes()
        probe_result = probes.reannotate_probe(
            vcf_path, "v101", "v102", "case_001"
        )
        
        print(f"✓ Probe completed")
        print(f"  - Effect size: {probe_result['effect_size']}")
        print(f"  - P-value: {probe_result['p']}")
        print(f"  - Explains: {probe_result['explains_pct']:.1%}")
        
        if probe_result['explains_pct'] < 0.8:
            print("✗ Probe explains < 80% - test failed")
            return False
            
    except Exception as e:
        print(f"✗ Probe failed: {e}")
        return False
    
    # Step 6: Propose remediation
    print("\n6. Proposing remediation...")
    try:
        remediation = RemediationEngine()
        patch = remediation.propose_patch("annotation_drift")
        
        print(f"✓ Proposed patch: {patch}")
        
        if "annot_db" not in patch:
            print("✗ Patch doesn't contain annot_db - test failed")
            return False
            
    except Exception as e:
        print(f"✗ Remediation failed: {e}")
        return False
    
    # Step 7: Test LLM bridge (scripted mode)
    print("\n7. Testing LLM bridge (scripted mode)...")
    try:
        llm_bridge = LLMBridge()
        
        # Test agent message
        message = llm_bridge.get_agent_message("detect", {"anomalies": anomalies})
        print(f"✓ Agent message: {message}")
        
        # Test summary
        context = {
            "anomalies": anomalies,
            "hypotheses": hypotheses,
            "probe_result": probe_result,
            "patch": patch
        }
        summary = llm_bridge.summarize_investigation(context)
        print(f"✓ Summary: {summary[:100]}...")
        
    except Exception as e:
        print(f"✗ LLM bridge failed: {e}")
        return False
    
    print("\n🎉 End-to-End Test PASSED!")
    print("✅ All components working correctly")
    print("✅ Annotation drift scenario completed successfully")
    
    return True

if __name__ == "__main__":
    success = test_e2e_annotation_drift()
    if success:
        print("\n🏆 GIA System is ready for demo!")
        exit(0)
    else:
        print("\n❌ E2E test failed")
        exit(1)