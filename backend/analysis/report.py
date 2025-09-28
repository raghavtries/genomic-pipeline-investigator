"""
Remediation and validation utilities for genomics pipeline fixes.
Implements patch proposals and micro-cohort validation.
"""
import json
import os
from typing import Dict, List, Any
from pathlib import Path
import subprocess
from .pipeline import align, call_variants, annotate, predict
from .detectors import DriftDetector

class RemediationEngine:
    """Handles remediation proposals and validation."""
    
    def __init__(self, output_dir: str = "runs"):
        self.output_dir = Path(output_dir)
        self.detector = DriftDetector()
    
    def propose_patch(self, hypothesis_id: str) -> Dict[str, Any]:
        """Propose a remediation patch based on hypothesis."""
        patches = {
            "annotation_drift": {
                "annot_db": "vep_v101",
                "transcript_policy": "canonical"
            },
            "caller_drift": {
                "caller_tag": "bcf_1.10",
                "min_qual": 20
            },
            "reference_drift": {
                "reference_build": "grch37",
                "standardize_build": True
            },
            "mapping_bias": {
                "min_coverage": 25,
                "softclip_threshold": 0.1
            },
            "schema_mismatch": {
                "schema_map": {
                    "missense": "missense_variant",
                    "synonymous": "synonymous_variant"
                },
                "impute_missing": True
            },
            "batch_effect": {
                "normalize_batch": True,
                "batch_correction": "combat"
            }
        }
        
        return patches.get(hypothesis_id, {})
    
    def apply_patch_on_microcohort(self, patch: Dict[str, Any], 
                                 microcohort_manifest: str) -> Dict[str, Any]:
        """Apply patch on micro-cohort and validate results."""
        # Load micro-cohort manifest
        with open(microcohort_manifest, 'r') as f:
            manifest = json.load(f)
        
        validation_dir = self.output_dir / "validation"
        validation_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            "samples_processed": 0,
            "samples_passed": 0,
            "metrics_restored": False,
            "drift_resolved": False,
            "details": {}
        }
        
        # Process each sample in micro-cohort
        for sample in manifest.get("samples", []):
            sample_id = sample["id"]
            sample_dir = validation_dir / sample_id
            sample_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Apply patch and run pipeline
                result = self._run_patched_pipeline(sample, patch, sample_dir)
                
                if result["success"]:
                    results["samples_passed"] += 1
                    
                    # Check if drift is resolved
                    if self._check_drift_resolved(result["metrics"]):
                        results["drift_resolved"] = True
                
                results["samples_processed"] += 1
                results["details"][sample_id] = result
                
            except Exception as e:
                results["details"][sample_id] = {
                    "success": False,
                    "error": str(e)
                }
                results["samples_processed"] += 1
        
        # Overall validation
        if results["samples_passed"] > 0:
            results["metrics_restored"] = True
        
        # Save validation results
        validation_file = validation_dir / "validation_results.json"
        with open(validation_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        results["validation_file"] = str(validation_file)
        return results
    
    def _run_patched_pipeline(self, sample: Dict[str, Any], patch: Dict[str, Any], 
                            output_dir: Path) -> Dict[str, Any]:
        """Run pipeline with applied patch."""
        result = {
            "success": False,
            "metrics": {},
            "artifacts": []
        }
        
        try:
            # Extract sample paths
            fq1 = sample["fq1"]
            fq2 = sample["fq2"]
            ref = sample.get("reference", "data/refs/grch37/chr21.fa")
            
            # Apply patch parameters
            caller_tag = patch.get("caller_tag", "bcftools")
            annot_db = patch.get("annot_db", "vep_v101")
            transcript_policy = patch.get("transcript_policy", "canonical")
            
            # Run pipeline stages
            bam_path, align_metrics = align(fq1, fq2, ref, str(output_dir / "align"))
            result["metrics"]["align"] = align_metrics
            
            vcf_path, call_metrics = call_variants(
                bam_path, ref, caller_tag, str(output_dir / "call")
            )
            result["metrics"]["call"] = call_metrics
            
            annot_vcf, annot_metrics = annotate(
                vcf_path, "vep", annot_db, transcript_policy, 
                str(output_dir / "annotate")
            )
            result["metrics"]["annotate"] = annot_metrics
            
            # Store artifacts
            result["artifacts"] = [
                str(bam_path),
                str(vcf_path), 
                str(annot_vcf)
            ]
            
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _check_drift_resolved(self, metrics: Dict[str, Any]) -> bool:
        """Check if drift is resolved based on metrics."""
        # Simplified implementation - would use actual drift detection
        # For now, assume drift is resolved if no critical anomalies
        
        # Check alignment metrics
        if "align" in metrics:
            align_metrics = metrics["align"]
            if align_metrics.get("softclip_rate", 0) > 0.1:
                return False
        
        # Check calling metrics  
        if "call" in metrics:
            call_metrics = metrics["call"]
            if abs(call_metrics.get("titv", 2.1) - 2.1) > 0.2:
                return False
        
        # Check annotation metrics
        if "annotate" in metrics:
            annot_metrics = metrics["annotate"]
            clinvar_counts = annot_metrics.get("clinvar_counts", {})
            if clinvar_counts.get("pathogenic", 0) < 10:
                return False
        
        return True
    
    def generate_remediation_report(self, case_id: str, hypothesis: str, 
                                  patch: Dict[str, Any], validation_results: Dict[str, Any]) -> str:
        """Generate comprehensive remediation report."""
        report = {
            "case_id": case_id,
            "hypothesis": hypothesis,
            "patch_applied": patch,
            "validation_summary": {
                "samples_processed": validation_results["samples_processed"],
                "samples_passed": validation_results["samples_passed"],
                "success_rate": validation_results["samples_passed"] / max(validation_results["samples_processed"], 1),
                "drift_resolved": validation_results["drift_resolved"]
            },
            "recommendations": self._generate_recommendations(validation_results),
            "next_steps": self._generate_next_steps(validation_results)
        }
        
        # Save report
        report_file = self.output_dir / case_id / "remediation_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return str(report_file)
    
    def _generate_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        if validation_results["drift_resolved"]:
            recommendations.append("✅ Drift successfully resolved - patch is effective")
            recommendations.append("📋 Consider implementing patch in production pipeline")
        else:
            recommendations.append("⚠️ Drift not fully resolved - consider alternative patches")
            recommendations.append("🔍 Investigate additional factors contributing to drift")
        
        if validation_results["samples_passed"] < validation_results["samples_processed"]:
            recommendations.append("⚠️ Some samples failed - check patch compatibility")
        
        return recommendations
    
    def _generate_next_steps(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate next steps based on validation results."""
        next_steps = []
        
        if validation_results["drift_resolved"]:
            next_steps.append("Deploy patch to production environment")
            next_steps.append("Monitor pipeline metrics for continued stability")
            next_steps.append("Update documentation with new parameters")
        else:
            next_steps.append("Try alternative remediation strategies")
            next_steps.append("Investigate root cause further")
            next_steps.append("Consider manual intervention if automated fixes fail")
        
        return next_steps