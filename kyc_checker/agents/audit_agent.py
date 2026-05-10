"""
Agent 7 — Audit Logger
Creates a structured, timestamped compliance audit record.
"""

import json
from datetime import datetime
from agents.base_agent import BaseAgent


SYSTEM_PROMPT = """You are a Compliance Audit Logger Agent for a KYC system.
Generate a structured audit trail entry suitable for regulatory compliance (RBI/SEBI standards).
The record must be complete, tamper-evident, and machine-readable.

Respond ONLY with a valid JSON object:
- audit_id: string (format: KYC-YYYYMMDD-XXXX where XXXX is random 4 digits)
- timestamp: ISO 8601 timestamp
- case_ref: string
- regulatory_framework: list of applicable regulations
- data_retention_years: integer
- consent_recorded: boolean
- processing_basis: string (legal basis for processing)
- agents_executed: list of agent names
- decision_trail: brief dict summarising each agent's verdict
- compliance_flags: list of any compliance concerns
- summary: one sentence
"""


class AuditAgent(BaseAgent):
    name = "audit_agent"

    def run(self, context: dict) -> dict:
        customer  = context["customer"]
        meta      = context.get("meta", {})
        decision  = context.get("decision_agent", {})
        doc       = context.get("document_agent", {})
        auth      = context.get("authenticity_agent", {})
        face      = context.get("face_match_agent", {})
        elig      = context.get("eligibility_agent", {})
        fraud     = context.get("fraud_agent", {})

        user_prompt = f"""
Generate a compliance audit log for the following KYC case:

Customer: {customer.get('full_name')}
DOB: {customer.get('dob')}
Product: {customer.get('product_type')}
Final Decision: {decision.get('decision', 'N/A')}
Processing Timestamp: {datetime.utcnow().isoformat()}

Agent verdicts:
- Document: {doc.get('validation_status','N/A')}
- Authenticity: {auth.get('verdict','N/A')}
- Face Match: {face.get('overall_verdict', face.get('face_match_result', 'N/A'))}
- Eligibility: {elig.get('overall_eligibility','N/A')}
- Fraud/Sanctions: {fraud.get('risk_level','N/A')} risk
- Final Decision: {decision.get('decision','N/A')} ({decision.get('confidence_score',0):.1f}% confidence)

Generate the full audit record as JSON.
"""

        result = self.groq.chat_json(SYSTEM_PROMPT, user_prompt)

        # Build the full log to persist / display
        full_log = {
            "kyc_audit": result,
            "customer_snapshot": {
                "name":     customer.get("full_name"),
                "dob":      customer.get("dob"),
                "doc_type": customer.get("doc_type"),
                "product":  customer.get("product_type"),
                "state":    customer.get("state"),
            },
            "pipeline_summary": {
                "document_validation":  doc.get("validation_status"),
                "authenticity_verdict": auth.get("verdict"),
                "face_match":           face.get("overall_verdict", face.get("face_match_result")),
                "eligibility":          elig.get("overall_eligibility"),
                "fraud_risk":           fraud.get("risk_level"),
                "final_decision":       decision.get("decision"),
                "confidence":           decision.get("confidence_score"),
                "autonomous_actions":   len(face.get("autonomous_actions", [])),
                "correlation_id":       meta.get("correlation_id"),
                "runtime_framework":    meta.get("runtime_framework"),
            },
        }

        return {"log": full_log, "summary": f"Audit record {result.get('audit_id','N/A')} created."}
