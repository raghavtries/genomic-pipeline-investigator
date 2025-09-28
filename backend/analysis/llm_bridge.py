"""
LLM bridge for scripted and LLM mode switching.
Handles text generation and hypothesis ranking with fallback to scripted content.
"""
import os
import json
from typing import Dict, List, Any
from pathlib import Path
from .config import Config

# Optional openai import
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class LLMBridge:
    """Bridges LLM calls with fallback to scripted content."""
    
    def __init__(self):
        self.config = Config()
        self.use_llm = os.getenv("USE_LLM", "false").lower() == "true"
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        
        if self.use_llm and self.api_key and OPENAI_AVAILABLE:
            openai.api_key = self.api_key
    
    def get_agent_message(self, step: str, context: Dict[str, Any]) -> str:
        """Get agent message for a given step."""
        if self.use_llm and self.api_key and OPENAI_AVAILABLE:
            return self._get_llm_message(step, context)
        else:
            return self._get_scripted_message(step, context)
    
    def rank_hypotheses_with_llm(self, anomalies: Dict[str, Any], 
                               kg_delta: Dict[str, Any], 
                               candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank hypotheses using LLM or fallback to scripted."""
        if self.use_llm and self.api_key and OPENAI_AVAILABLE:
            return self._rank_hypotheses_llm(anomalies, kg_delta, candidates)
        else:
            return self._rank_hypotheses_scripted(anomalies, kg_delta, candidates)
    
    def summarize_investigation(self, context: Dict[str, Any]) -> str:
        """Generate investigation summary."""
        if self.use_llm and self.api_key and OPENAI_AVAILABLE:
            return self._summarize_llm(context)
        else:
            return self._summarize_scripted(context)
    
    def _get_llm_message(self, step: str, context: Dict[str, Any]) -> str:
        """Generate message using LLM."""
        try:
            prompt = self._build_prompt(step, context)
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a genomics pipeline investigator agent. Provide concise, technical messages about pipeline drift detection and investigation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠ LLM fallback: {e}")
            return self._get_scripted_message(step, context)
    
    def _get_scripted_message(self, step: str, context: Dict[str, Any]) -> str:
        """Get scripted message for step."""
        scripted_file = Path("scripts/scripted/annotation_drift.json")
        
        if scripted_file.exists():
            with open(scripted_file, 'r') as f:
                scripted_data = json.load(f)
            
            agent_log = scripted_data.get("agent_log", [])
            for entry in agent_log:
                if entry.get("step") == step:
                    return entry.get("msg", f"Processing {step}...")
        
        # Fallback messages
        fallback_messages = {
            "detect": "🔍 Analyzing pipeline metrics for drift...",
            "hypothesize": "🧠 Generating hypotheses based on anomalies...",
            "plan": "📋 Planning investigation strategy...",
            "probe": "🔬 Running counterfactual probe...",
            "result": "📊 Analyzing probe results...",
            "remediate": "🔧 Proposing remediation strategy...",
            "validate": "✅ Validating fix on micro-cohort..."
        }
        
        return fallback_messages.get(step, f"Processing {step}...")
    
    def _rank_hypotheses_llm(self, anomalies: Dict[str, Any], 
                           kg_delta: Dict[str, Any], 
                           candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank hypotheses using LLM."""
        try:
            prompt = f"""
            Rank these hypotheses for genomics pipeline drift:
            
            Anomalies: {json.dumps(anomalies, indent=2)}
            Knowledge Graph Changes: {json.dumps(kg_delta, indent=2)}
            Candidate Hypotheses: {json.dumps(candidates, indent=2)}
            
            Return JSON with ranked hypotheses including confidence scores.
            """
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a genomics expert. Rank hypotheses based on evidence and return JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.2
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("hypotheses", candidates)
            
        except Exception as e:
            print(f"⚠ LLM fallback: {e}")
            return self._rank_hypotheses_scripted(anomalies, kg_delta, candidates)
    
    def _rank_hypotheses_scripted(self, anomalies: Dict[str, Any], 
                                kg_delta: Dict[str, Any], 
                                candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank hypotheses using scripted logic."""
        # Load scripted hypotheses
        scripted_file = Path("scripts/scripted/annotation_drift.json")
        
        if scripted_file.exists():
            with open(scripted_file, 'r') as f:
                scripted_data = json.load(f)
            
            return scripted_data.get("hypotheses", candidates)
        
        # Fallback to simple ranking
        return candidates
    
    def _summarize_llm(self, context: Dict[str, Any]) -> str:
        """Generate summary using LLM."""
        try:
            prompt = f"""
            Summarize this genomics pipeline investigation:
            
            Context: {json.dumps(context, indent=2)}
            
            Provide a concise summary including root cause, evidence, and resolution.
            """
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a genomics expert. Provide clear, technical summaries of pipeline investigations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠ LLM fallback: {e}")
            return self._summarize_scripted(context)
    
    def _summarize_scripted(self, context: Dict[str, Any]) -> str:
        """Generate scripted summary."""
        scripted_file = Path("scripts/scripted/annotation_drift.json")
        
        if scripted_file.exists():
            with open(scripted_file, 'r') as f:
                scripted_data = json.load(f)
            
            return scripted_data.get("summary", "Investigation completed.")
        
        return "Investigation completed with scripted fallback."
    
    def _build_prompt(self, step: str, context: Dict[str, Any]) -> str:
        """Build prompt for LLM based on step and context."""
        prompts = {
            "detect": f"Generate a message about drift detection. Context: {context}",
            "hypothesize": f"Generate a message about hypothesis generation. Context: {context}",
            "plan": f"Generate a message about investigation planning. Context: {context}",
            "probe": f"Generate a message about running probes. Context: {context}",
            "result": f"Generate a message about probe results. Context: {context}",
            "remediate": f"Generate a message about remediation. Context: {context}",
            "validate": f"Generate a message about validation. Context: {context}"
        }
        
        return prompts.get(step, f"Generate a message for step: {step}. Context: {context}")