"""
FastAPI main application for GIA system.
Implements all required endpoints with proper error handling.
"""
import os
import json
import uuid
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

from .schemas import (
    RunRequest, RunResponse, CheckDriftRequest, CheckDriftResponse,
    NextProbeRequest, NextProbeResponse, RunProbeRequest, ProbeResult,
    RemediateRequest, RemediateResponse, SummaryRequest, SummaryResponse,
    EventLog, InvestigationState, LLMAnalysis
)

# Import analysis modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from analysis.pipeline import align, call_variants, annotate, predict
from analysis.detectors import DriftDetector
from analysis.kg import KnowledgeGraph
from analysis.hypotheses import HypothesisRanker
from analysis.probes import CounterfactualProbes
from analysis.report import RemediationEngine
from analysis.llm_bridge import LLMBridge
from analysis.llm_analysis import LLMAnalyzer
from analysis.config import Config

app = FastAPI(title="Genomics Investigator Agent", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
detector = DriftDetector()
kg_builder = KnowledgeGraph()
hypothesis_ranker = HypothesisRanker()
probes = CounterfactualProbes()
remediation = RemediationEngine()
llm_bridge = LLMBridge()
llm_analyzer = LLMAnalyzer()
config = Config()

# In-memory state storage (in production, use database)
investigations = {}
run_artifacts = {}

@app.post("/api/run", response_model=RunResponse)
async def run_pipeline(request: RunRequest):
    """Run genomics pipeline and return artifacts."""
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    start_time = time.time()
    
    try:
        # Create run directory
        run_dir = Path("runs") / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Run pipeline stages
        bam_path, align_metrics = align(
            str(request.fq1_path), str(request.fq2_path), str(request.reference), 
            str(run_dir / "align")
        )
        
        vcf_path, call_metrics = call_variants(
            bam_path, str(request.reference), str(request.caller_tag), 
            str(run_dir / "call")
        )
        
        annot_vcf, annot_metrics = annotate(
            vcf_path, str(request.annotator), str(request.db_version), 
            str(request.transcript_policy), str(run_dir / "annotate")
        )
        
        predictions, pred_metrics = predict(
            annot_vcf, "models/pathogenicity_model.pkl", {}, 
            str(run_dir / "predict")
        )
        
        # Store metrics
        all_metrics = {
            "align": align_metrics,
            "call": call_metrics,
            "annotate": annot_metrics,
            "predict": pred_metrics
        }
        
        metrics_file = run_dir / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(all_metrics, f, indent=2)
        
        # Build knowledge graph
        kg_builder.add_run_node(run_id, {"sample_id": request.sample_id})
        ref_node = kg_builder.add_reference_node(request.reference)
        aligner_node = kg_builder.add_aligner_node("bwa")
        caller_node = kg_builder.add_caller_node(request.caller_tag)
        vcf_node = kg_builder.add_vcf_node(vcf_path)
        annotator_node = kg_builder.add_annotator_node(request.annotator, request.db_version)
        
        # Add edges
        kg_builder.add_edge(f"run_{run_id}", ref_node, "uses")
        kg_builder.add_edge(f"run_{run_id}", aligner_node, "uses")
        kg_builder.add_edge(aligner_node, vcf_node, "produced_by")
        kg_builder.add_edge(caller_node, vcf_node, "produced_by")
        kg_builder.add_edge(annotator_node, vcf_node, "uses")
        
        # Save knowledge graph
        kg_file = kg_builder.save_graph(run_id, str(run_dir))
        
        # Store run artifacts
        run_artifacts[run_id] = {
            "metrics_file": str(metrics_file),
            "kg_file": kg_file,
            "artifacts": {
                "bam": bam_path,
                "vcf": vcf_path,
                "annot_vcf": annot_vcf
            }
        }
        
        # Log event
        duration_ms = int((time.time() - start_time) * 1000)
        log_event(run_id, "run_pipeline", {"request": request.dict()}, 
                 f"Pipeline completed successfully", duration_ms)
        
        return RunResponse(
            run_id=run_id,
            metrics=str(metrics_file),
            kg=kg_file,
            status="ok"
        )
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        log_event(run_id, "run_pipeline_error", {"error": str(e)}, 
                 f"Pipeline failed: {str(e)}", duration_ms)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/check_drift", response_model=CheckDriftResponse)
async def check_drift(request: CheckDriftRequest):
    """Check for drift in pipeline metrics."""
    start_time = time.time()
    
    try:
        # Load run metrics
        if request.run_id not in run_artifacts:
            raise HTTPException(status_code=404, detail="Run not found")
        
        metrics_file = run_artifacts[request.run_id]["metrics_file"]
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        # Detect drift for each stage
        all_anomalies = []
        for stage, stage_metrics in metrics.items():
            anomalies = detector.detect_drift(request.run_id, stage, stage_metrics)
            all_anomalies.extend(anomalies)
        
        # Determine if investigation should be opened
        open_investigation = len(all_anomalies) > 0
        case_id = None
        llm_analysis = None
        
        if open_investigation:
            case_id = f"case_{uuid.uuid4().hex[:8]}"
            investigations[case_id] = InvestigationState(
                case_id=case_id,
                state="DETECT",
                anomalies=all_anomalies
            )
            
            # Generate LLM analysis
            print(f"🧠 {llm_analyzer.get_model_info()}")
            evidence_parts = llm_analyzer.analyze_evidence(all_anomalies, metrics)
            remediation_parts = llm_analyzer.analyze_remediation(all_anomalies, [])
            current_actions = llm_analyzer.analyze_current_actions("DETECT", "drift_analysis")
            
            llm_analysis = LLMAnalysis(
                evidence_parts=evidence_parts,
                remediation_parts=remediation_parts,
                current_actions=current_actions
            )
        
        # Log event
        duration_ms = int((time.time() - start_time) * 1000)
        log_event(request.run_id, "check_drift", {"baseline": request.baseline}, 
                 f"Found {len(all_anomalies)} anomalies", duration_ms)
        
        return CheckDriftResponse(
            anomalies=all_anomalies,
            open_investigation=open_investigation,
            case_id=case_id,
            llm_analysis=llm_analysis
        )
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        log_event(request.run_id, "check_drift_error", {"error": str(e)}, 
                 f"Drift check failed: {str(e)}", duration_ms)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/next_probe", response_model=NextProbeResponse)
async def next_probe(request: NextProbeRequest):
    """Get next probe to run for investigation."""
    start_time = time.time()
    
    try:
        if request.case_id not in investigations:
            raise HTTPException(status_code=404, detail="Case not found")
        
        case = investigations[request.case_id]
        
        # Rank hypotheses if not done yet
        if not case.hypotheses:
            kg_delta = {"db_version_changed": True}  # Simplified
            case.hypotheses = hypothesis_ranker.rank_hypotheses(
                kg_delta, case.anomalies
            )
        
        # Select next probe based on priority
        probe_type = config.probe_priorities[case.probe_count % len(config.probe_priorities)]
        
        # Create probe plan
        plan = {
            "hypothesis": case.hypotheses[0]["id"] if case.hypotheses else "annotation_drift",
            "hypotheses": case.hypotheses,  # Return all hypotheses
            "probe": probe_type,
            "args": {
                "case_id": request.case_id,
                "probe_type": probe_type
            }
        }
        
        # Update state
        case.state = "PLAN"
        case.current_hypothesis = plan["hypothesis"]
        
        # Log event
        duration_ms = int((time.time() - start_time) * 1000)
        log_event(request.case_id, "next_probe", {"probe": probe_type}, 
                 f"Planned {probe_type} probe", duration_ms)
        
        return NextProbeResponse(plan=plan)
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        log_event(request.case_id, "next_probe_error", {"error": str(e)}, 
                 f"Next probe failed: {str(e)}", duration_ms)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run_probe", response_model=ProbeResult)
async def run_probe(request: RunProbeRequest):
    """Run a counterfactual probe."""
    start_time = time.time()
    
    try:
        if request.case_id not in investigations:
            raise HTTPException(status_code=404, detail="Case not found")
        
        case = investigations[request.case_id]
        
        # Run appropriate probe
        if request.probe == "reannotate":
            result = probes.reannotate_probe(
                "data/inputs/sample.vcf", "v101", "v102", request.case_id
            )
        elif request.probe == "realign_recall_locus":
            result = probes.realign_recall_locus_probe(
                "data/inputs/sample_R1.fastq.gz", "data/inputs/sample_R2.fastq.gz",
                "data/refs/grch37/chr21.fa", "data/refs/grch38/chr21.fa",
                "data/truth/giab/giab_chr21.vcf.gz", request.case_id
            )
        elif request.probe == "downsample_noise":
            result = probes.downsample_noise_probe(
                "data/inputs/sample.bam", "data/refs/grch37/chr21.fa", request.case_id
            )
        elif request.probe == "caller_version":
            result = probes.caller_version_probe(
                "data/inputs/sample.bam", "data/refs/grch37/chr21.fa",
                "bcftools_old", "bcftools_new", request.case_id
            )
        elif request.probe == "schema_normalize":
            result = probes.schema_normalize_probe(
                "data/inputs/sample_annot.vcf", {"missense": "missense_variant"},
                "models/pathogenicity_model.pkl", request.case_id
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown probe: {request.probe}")
        
        # Update case state
        case.state = "ASSESS"
        case.probe_count += 1
        case.probe_results.append(ProbeResult(**result))
        
        # Check convergence
        if config.is_converged(result["explains_pct"], result["p"]):
            case.state = "CONVERGED"
        
        # Log event
        duration_ms = int((time.time() - start_time) * 1000)
        log_event(request.case_id, "run_probe", {"probe": request.probe}, 
                 f"Probe completed: {result['explains_pct']:.2f} explains", duration_ms)
        
        return ProbeResult(**result)
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        log_event(request.case_id, "run_probe_error", {"error": str(e)}, 
                 f"Probe failed: {str(e)}", duration_ms)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/remediate", response_model=RemediateResponse)
async def remediate(request: RemediateRequest):
    """Apply remediation patch and validate."""
    start_time = time.time()
    
    try:
        if request.case_id not in investigations:
            raise HTTPException(status_code=404, detail="Case not found")
        
        case = investigations[request.case_id]
        
        # Apply remediation
        validation_results = remediation.apply_patch_on_microcohort(
            request.patch, "data/microcohort/cohort_manifest.json"
        )
        
        # Update case state
        case.state = "VALIDATE"
        case.remediation_applied = request.patch
        case.validation_results = validation_results
        
        # Log event
        duration_ms = int((time.time() - start_time) * 1000)
        log_event(request.case_id, "remediate", {"patch": request.patch}, 
                 f"Remediation applied: {validation_results['samples_passed']} samples passed", duration_ms)
        
        return RemediateResponse(
            replay_passed=validation_results["samples_passed"] > 0,
            metrics_restored=validation_results["metrics_restored"],
            details=validation_results.get("validation_file", "")
        )
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        log_event(request.case_id, "remediate_error", {"error": str(e)}, 
                 f"Remediation failed: {str(e)}", duration_ms)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/kg/{run_id}")
async def get_kg(run_id: str):
    """Get knowledge graph for a run."""
    try:
        if run_id not in run_artifacts:
            raise HTTPException(status_code=404, detail="Run not found")
        
        kg_file = run_artifacts[run_id]["kg_file"]
        with open(kg_file, 'r') as f:
            kg_data = json.load(f)
        
        return kg_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events")
async def get_events(case_id: str):
    """Get event stream for a case."""
    try:
        events_file = Path("runs") / case_id / "events.jsonl"
        
        if not events_file.exists():
            return []
        
        events = []
        with open(events_file, 'r') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        
        return events
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/summary", response_model=SummaryResponse)
async def get_summary(request: SummaryRequest):
    """Get investigation summary."""
    start_time = time.time()
    
    try:
        if request.case_id not in investigations:
            raise HTTPException(status_code=404, detail="Case not found")
        
        case = investigations[request.case_id]
        
        # Generate summary context
        context = {
            "case_id": request.case_id,
            "anomalies": case.anomalies,
            "hypotheses": case.hypotheses,
            "probe_results": [result.dict() for result in case.probe_results],
            "remediation": case.remediation_applied,
            "validation": case.validation_results
        }
        
        # Get summary from LLM bridge
        summary = llm_bridge.summarize_investigation(context)
        
        # Update state
        case.state = "SUMMARY"
        
        # Log event
        duration_ms = int((time.time() - start_time) * 1000)
        log_event(request.case_id, "summary", {}, 
                 f"Summary generated: {len(summary)} chars", duration_ms)
        
        return SummaryResponse(summary=summary)
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        log_event(request.case_id, "summary_error", {"error": str(e)}, 
                 f"Summary failed: {str(e)}", duration_ms)
        raise HTTPException(status_code=500, detail=str(e))

def log_event(case_id: str, action: str, args: Dict[str, Any], 
              result_summary: str, duration_ms: int):
    """Log an event to the events.jsonl file."""
    try:
        events_file = Path("runs") / case_id / "events.jsonl"
        events_file.parent.mkdir(parents=True, exist_ok=True)
        
        event = EventLog(
            timestamp=datetime.now(),
            action=action,
            args_hash=hashlib.md5(json.dumps(args, sort_keys=True).encode()).hexdigest()[:8],
            result_summary=result_summary,
            duration_ms=duration_ms
        )
        
        with open(events_file, 'a') as f:
            f.write(event.json() + "\n")
            
    except Exception as e:
        print(f"Failed to log event: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)