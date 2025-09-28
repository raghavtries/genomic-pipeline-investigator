"""
LLM-powered analysis for genomics pipeline drift investigation.
Uses Gemini via LangChain to provide structured analysis.
"""
import os
import json
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

class LLMAnalyzer:
    """LLM-powered analysis for genomics drift investigation."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the LLM analyzer."""
        self.api_key = api_key or os.getenv("GEMINI_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_KEY environment variable is required")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=self.api_key,
            temperature=0.1
        )
    
    def analyze_evidence(self, anomalies: List[Dict[str, Any]], 
                        metrics: Dict[str, Any]) -> List[str]:
        """Generate 3-part evidence analysis."""
        # Optimized prompt - shorter and more focused
        prompt = f"""Analyze genomics drift: {anomalies[0]['metric']} (p={anomalies[0]['p']}, effect={anomalies[0]['effect']})

Provide 3 evidence parts:
1. Statistical: p-values, effect sizes
2. Clinical: pathogenic variants, coverage  
3. Technical: pipeline stages, versions

JSON: ["part1", "part2", "part3"]"""
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            json_str = content[json_start:json_end].strip()
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                # Extract text from dictionary values
                result = []
                for value in list(parsed.values())[:3]:
                    if isinstance(value, dict):
                        # Extract title or description from nested dict
                        text = value.get('title', value.get('description', str(value)))
                        result.append(text)
                    else:
                        result.append(str(value))
                return result
            return parsed[:3]
        else:
            return self._parse_evidence_response(content)
    
    def analyze_remediation(self, anomalies: List[Dict[str, Any]], 
                           hypotheses: List[Dict[str, Any]]) -> List[str]:
        """Generate 3-part remediation plan."""
        # Optimized prompt - shorter and more focused
        prompt = f"""Fix genomics drift: {anomalies[0]['metric']} in {anomalies[0]['stage']}

Provide 3 steps along with 5 lines of demo code output for each in the format of [$ Running remediation protocol... | $ Validating parameters... | ✓ Database version pinned to v101]:
1. Immediate fix 2 sentences (version pinning, parameters) with code in [] like $ Running remediation protocol... | $ Validating parameters...</div>
2. Validation 2 sentences  (re-run, compare results)  
3. Prevention 3 sentences (monitoring, alerts)

JSON: ["step1", "step2", "step3"]"""
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            json_str = content[json_start:json_end].strip()
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                # Extract text from dictionary values
                result = []
                for value in list(parsed.values())[:3]:
                    if isinstance(value, dict):
                        # Extract title or description from nested dict
                        text = value.get('title', value.get('description', str(value)))
                        result.append(text)
                    else:
                        result.append(str(value))
                return result
            return parsed[:3]
        else:
            return self._parse_remediation_response(content)
    
    def analyze_current_actions(self, case_state: str, 
                               current_step: str) -> List[str]:
        """Generate current action analysis."""
        # Optimized prompt - shorter and more focused
        prompt = f"""Genomics investigation: {case_state} - {current_step}

Current actions:
1. "Fixing: [what is being fixed]"
2. "Rerunning: [what is being re-executed]"  
3. "Found: [what was discovered]"

JSON: ["action1", "action2", "action3"]"""
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            json_str = content[json_start:json_end].strip()
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                # Extract text from dictionary values
                result = []
                for value in list(parsed.values())[:3]:
                    if isinstance(value, dict):
                        # Extract title or description from nested dict
                        text = value.get('title', value.get('description', str(value)))
                        result.append(text)
                    else:
                        result.append(str(value))
                return result
            return parsed[:3]
        else:
            return self._parse_current_actions_response(content)
    
    
    def _parse_evidence_response(self, content: str) -> List[str]:
        """Parse evidence response from LLM."""
        # Simple parsing - look for numbered items
        lines = content.split('\n')
        evidence = []
        for line in lines:
            if line.strip().startswith(('1.', '2.', '3.')):
                evidence.append(line.strip())
        return evidence[:3] if evidence else ["Evidence part 1: Statistical analysis", "Evidence part 2: Clinical evidence", "Evidence part 3: Technical evidence"]
    
    def _parse_remediation_response(self, content: str) -> List[str]:
        """Parse remediation response from LLM."""
        lines = content.split('\n')
        steps = []
        for line in lines:
            if line.strip().startswith(('1.', '2.', '3.')):
                steps.append(line.strip())
        return steps[:3] if steps else ["Step 1: Fix issue", "Step 2: Validate", "Step 3: Monitor"]
    
    def _parse_current_actions_response(self, content: str) -> List[str]:
        """Parse current actions response from LLM."""
        lines = content.split('\n')
        actions = []
        for line in lines:
            if any(prefix in line for prefix in ['Fixing:', 'Rerunning:', 'Found:', 'Execute:']):
                actions.append(line.strip())
        return actions[:4] if actions else ["Fixing: Processing", "Rerunning: Analysis", "Found: Results"]