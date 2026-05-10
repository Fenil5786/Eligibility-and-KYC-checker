"""
KYC Orchestrator — coordinates all specialist agents in sequence,
passing context between them and collecting a unified result.
"""

import time
import json
import uuid
import streamlit as st
from datetime import datetime
from typing import Any

from agents.document_agent      import DocumentExtractionAgent
from agents.authenticity_agent  import AuthenticityAgent
from agents.face_match_agent    import FaceMatchAgent
from agents.eligibility_agent   import EligibilityAgent
from agents.fraud_agent         import FraudSanctionsAgent
from agents.decision_agent      import DecisionAgent
from agents.audit_agent         import AuditAgent
from utils.groq_client          import GroqClient
from utils.microsoft_agentic_runtime import MicrosoftAgenticRuntime


class KYCOrchestrator:
    """
    Agentic orchestrator that runs all KYC agents sequentially,
    passing shared context between them.
    """

    def __init__(self, api_key: str, model: str):
        self.groq   = GroqClient(api_key=api_key, model=model)
        self.runtime = MicrosoftAgenticRuntime(enterprise_mode=True)
        self.agents = [
            DocumentExtractionAgent(self.groq),
            AuthenticityAgent(self.groq),
            FaceMatchAgent(self.groq),
            EligibilityAgent(self.groq),
            FraudSanctionsAgent(self.groq),
            DecisionAgent(self.groq),
            AuditAgent(self.groq),
        ]

    def run(self, customer_data: dict, steps: list, placeholders: list) -> dict:
        start_time = time.time()
        correlation_id = str(uuid.uuid4())
        runtime_meta = self.runtime.execution_meta(correlation_id)
        context: dict[str, Any] = {
            "customer": customer_data,
            "meta": {
                "correlation_id": correlation_id,
                "runtime_framework": runtime_meta.framework,
                "enterprise_mode": runtime_meta.enterprise_mode,
                "started_at": runtime_meta.started_at,
            },
        }
        agent_results: dict[str, Any] = {}

        for idx, (agent, (label, desc)) in enumerate(zip(self.agents, steps)):
            ph = placeholders[idx]
            ph.markdown(f"🔄 `{label}` — {desc}")

            try:
                retries = 0
                last_error = None
                result = None
                while retries < 2:
                    try:
                        result = self.runtime.invoke_agent(agent, context)
                        break
                    except Exception as e:
                        retries += 1
                        last_error = e
                if result is None and last_error is not None:
                    raise last_error

                context[agent.name] = result
                agent_results[label] = result

                status_icon = "✅"
                summary = result.get("summary", "Done") if isinstance(result, dict) else str(result)[:80]
                ph.markdown(f"{status_icon} `{label}` — {summary}")

            except Exception as e:
                ph.markdown(f"⚠️ `{label}` — Error: {str(e)[:100]}")
                context[agent.name] = {"error": str(e), "summary": "Agent failed"}
                agent_results[label] = {"error": str(e)}

            time.sleep(0.3)   # slight delay for visual effect

        elapsed = time.time() - start_time

        # Pull final outputs from DecisionAgent
        decision_result = context.get("decision_agent", {})
        audit_result    = context.get("audit_agent", {})

        return {
            "final_decision":  decision_result.get("decision", "REFER"),
            "confidence_score": decision_result.get("confidence_score", 0.0),
            "reasoning":        decision_result.get("reasoning", ""),
            "risk_factors":     decision_result.get("risk_factors", []),
            "agent_results":    agent_results,
            "audit_log":        audit_result.get("log", {}),
            "processing_time":  f"{elapsed:.1f}s",
            "correlation_id":   correlation_id,
            "framework":        runtime_meta.framework,
            "enterprise_mode":  runtime_meta.enterprise_mode,
        }
