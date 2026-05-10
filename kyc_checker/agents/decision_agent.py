"""
Agent 6 — Decision Agent
Synthesises all upstream agent results and issues a final verdict.
"""

from agents.base_agent import BaseAgent


SYSTEM_PROMPT = """You are the Final Decision Agent in a KYC verification pipeline.
You receive a consolidated summary of all upstream agent results and must produce a final decision.

Decision rules:
- AUTO-APPROVE: All checks pass, no fraud flags, eligibility met, documents genuine, face match OK
- AUTO-REJECT: Fake document, high fraud risk/sanctions hit, clearly ineligible, critical risk
- REFER: One or more agents uncertain, minor mismatches, medium risk, partial eligibility

Your reasoning must be clear, fair, and auditable.

Respond ONLY with a valid JSON object:
- decision: "APPROVE" | "REJECT" | "REFER"
- confidence_score: float 0-100
- reasoning: detailed paragraph explaining the decision (3-5 sentences)
- risk_factors: list of strings (key risk issues found)
- positive_factors: list of strings (what supported a positive assessment)
- recommended_action: string (what should happen next)
- human_review_required: boolean
- summary: one sentence
"""


class DecisionAgent(BaseAgent):
    name = "decision_agent"

    def run(self, context: dict) -> dict:
        doc      = context.get("document_agent", {})
        auth     = context.get("authenticity_agent", {})
        face     = context.get("face_match_agent", {})
        elig     = context.get("eligibility_agent", {})
        fraud    = context.get("fraud_agent", {})
        customer = context["customer"]

        user_prompt = f"""
=== CONSOLIDATED KYC REPORT ===

CUSTOMER: {customer.get('full_name')} | Product: {customer.get('product_type')}

DOCUMENT EXTRACTION:
  Validation Status: {doc.get('validation_status','N/A')}
  Completeness Score: {doc.get('completeness_score', 0)}
  Issues: {doc.get('issues', [])}

AUTHENTICITY:
  Verdict: {auth.get('verdict','N/A')}
  Authenticity Score: {auth.get('authenticity_score', 0)}
  Tamper Detected: {auth.get('tamper_detected', False)}
  Red Flags: {auth.get('red_flags', [])}

FACE MATCH:
  Result: {face.get('face_match_result','N/A')}
  Match Score: {face.get('match_score', 0)}
  Liveness: {face.get('liveness_check','N/A')}

ELIGIBILITY:
  Overall: {elig.get('overall_eligibility','N/A')}
  Score: {elig.get('eligibility_score', 0)}
  Failed Criteria: {elig.get('failed_criteria', [])}
  Passed Criteria: {elig.get('passed_criteria', [])}

FRAUD & SANCTIONS:
  Risk Level: {fraud.get('risk_level','N/A')}
  Risk Score: {fraud.get('risk_score', 0)}
  Sanctions Hit: {fraud.get('sanctions_hit', False)}
  Screening Passed: {fraud.get('screening_passed', True)}
  Watchlist Matches: {fraud.get('watchlist_matches', [])}

Make the final decision and return JSON.
"""

        result = self.groq.chat_json(SYSTEM_PROMPT, user_prompt)
        result.setdefault("summary", f"Decision: {result.get('decision','REFER')} | Confidence: {result.get('confidence_score',0):.1f}%")
        return result
