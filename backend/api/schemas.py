"""
Pydantic schemas for GIA API endpoints.
Defines request/response models for all API routes.
"""
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime

class RunRequest(BaseModel):
    """Request model for pipeline run."""
    sample_id: str
    fq1_path: str
    fq2_path: str
    reference: str = "data/refs/grch37/chr21.fa"
    caller_tag: str = "bcftools"
    annotator: str = "vep"
    db_version: str = "v101"
    transcript_policy: str = "canonical"

class RunResponse(BaseModel):
    """Response model for pipeline run."""
    run_id: str
    metrics: str
    kg: str
    status: str

class CheckDriftRequest(BaseModel):
    """Request model for drift checking."""
    run_id: str
    baseline: str = "rolling"

class LLMAnalysis(BaseModel):
    """LLM analysis model."""
    evidence_parts: List[str]
    remediation_parts: List[str]
    current_actions: List[str]

class CheckDriftResponse(BaseModel):
    """Response model for drift checking."""
    anomalies: List[Dict[str, Any]]
    open_investigation: bool
    case_id: Optional[str] = None
    llm_analysis: Optional[LLMAnalysis] = None

class NextProbeRequest(BaseModel):
    """Request model for next probe."""
    case_id: str

class NextProbeResponse(BaseModel):
    """Response model for next probe."""
    plan: Dict[str, Any]

class RunProbeRequest(BaseModel):
    """Request model for running probe."""
    case_id: str
    probe: str
    args: Dict[str, Any]

class ProbeResult(BaseModel):
    """Probe result model."""
    probe: str
    effect_size: float
    p: float
    explains_pct: float
    artifacts: Dict[str, Any]

class RemediateRequest(BaseModel):
    """Request model for remediation."""
    case_id: str
    patch: Dict[str, Any]

class RemediateResponse(BaseModel):
    """Response model for remediation."""
    replay_passed: bool
    metrics_restored: bool
    details: str

class SummaryRequest(BaseModel):
    """Request model for summary."""
    case_id: str

class SummaryResponse(BaseModel):
    """Response model for summary."""
    summary: str

class EventLog(BaseModel):
    """Event log entry."""
    timestamp: datetime
    action: str
    args_hash: str
    result_summary: str
    duration_ms: int

class InvestigationState(BaseModel):
    """Investigation state model."""
    case_id: str
    state: str  # DETECT, PLAN, RUN_PROBE, ASSESS, CONVERGED, REMEDIATE, VALIDATE, SUMMARY
    current_hypothesis: Optional[str] = None
    probe_count: int = 0
    anomalies: List[Dict[str, Any]] = []
    hypotheses: List[Dict[str, Any]] = []
    probe_results: List[ProbeResult] = []
    remediation_applied: Optional[Dict[str, Any]] = None
    validation_results: Optional[Dict[str, Any]] = None