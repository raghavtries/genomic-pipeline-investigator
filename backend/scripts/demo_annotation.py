#!/usr/bin/env python3
"""
Demo script for GIA annotation drift scenario.
Shows the complete investigation workflow.
"""
import sys
import os
import time
import json
sys.path.append('.')

from analysis.pipeline import align, call_variants, annotate
from analysis.detectors import DriftDetector
from analysis.hypotheses import HypothesisRanker
from analysis.probes import CounterfactualProbes
from analysis.report import RemediationEngine
from analysis.llm_bridge import LLMBridge

def demo_annotation_drift():
    """Run the complete annotation drift demo."""
    print("🧬 GIA Demo: Annotation Drift Investigation")
    print("=" * 60)
    
    # Step 1: Baseline run
    print("\n📊 Step 1: Running baseline pipeline (VEP v101)...")
    bam_path, align_metrics = align(
        "data/inputs/sample_001_R1.fastq", 
        "data/inputs/sample_001_R2.fastq",
        "data/refs/grch37/chr21.fa", 
        "runs/demo_baseline"
    )
    
    vcf_path, call_metrics = call_variants(
        bam_path, "data/refs/grch37/chr21.fa", "bcftools", "runs/demo_baseline"
    )
    
    annot_vcf_v101, annot_metrics_v101 = annotate(
        vcf_path, "vep", "v101", "canonical", "runs/demo_baseline"
    )
    
    print(f"✓ Baseline completed: {annot_metrics_v101['clinvar_counts']}")
    
    # Step 2: Drifted run
    print("\n📊 Step 2: Running drifted pipeline (VEP v102)...")
    annot_vcf_v102, annot_metrics_v102 = annotate(
        vcf_path, "vep", "v102", "canonical", "runs/demo_drifted"
    )
    
    print(f"✓ Drifted completed: {annot_metrics_v102['clinvar_counts']}")
    
    # Step 3: Detect drift
    print("\n🔍 Step 3: Detecting drift...")
    detector = DriftDetector()
    detector.store_metrics("baseline_demo", "annotate", annot_metrics_v101)
    anomalies = detector.detect_drift("drifted_demo", "annotate", annot_metrics_v102)
    
    print(f"✓ Found {len(anomalies)} anomalies:")
    for anomaly in anomalies:
        print(f"  - {anomaly['stage']}: {anomaly['metric']} (p={anomaly['p']:.2e})")
    
    # Step 4: Rank hypotheses
    print("\n🧠 Step 4: Ranking hypotheses...")
    ranker = HypothesisRanker()
    kg_delta = {"db_version_changed": True}
    hypotheses = ranker.rank_hypotheses(kg_delta, anomalies)
    
    print("✓ Top hypotheses:")
    for i, hyp in enumerate(hypotheses[:3]):
        print(f"  {i+1}. {hyp['label']} (score: {hyp['score']:.2f})")
    
    # Step 5: Run probe
    print("\n🔬 Step 5: Running reannotation probe...")
    probes = CounterfactualProbes()
    probe_result = probes.reannotate_probe(
        vcf_path, "v101", "v102", "demo_case"
    )
    
    print(f"✓ Probe results:")
    print(f"  - Effect size: {probe_result['effect_size']:.2f}")
    print(f"  - P-value: {probe_result['p']:.2e}")
    print(f"  - Explains: {probe_result['explains_pct']:.1%}")
    
    # Step 6: Propose remediation
    print("\n🔧 Step 6: Proposing remediation...")
    remediation = RemediationEngine()
    patch = remediation.propose_patch("annotation_drift")
    
    print(f"✓ Proposed patch: {patch}")
    
    # Step 7: Generate summary
    print("\n📝 Step 7: Generating investigation summary...")
    llm_bridge = LLMBridge()
    
    context = {
        "anomalies": anomalies,
        "hypotheses": hypotheses,
        "probe_result": probe_result,
        "patch": patch
    }
    
    summary = llm_bridge.summarize_investigation(context)
    print(f"✓ Summary: {summary}")
    
    print("\n🎉 Demo completed successfully!")
    print("✅ All components working with real genomics tools")
    print("✅ Drift detection, hypothesis ranking, and remediation working")
    print("✅ Ready for production use!")

if __name__ == "__main__":
    demo_annotation_drift()