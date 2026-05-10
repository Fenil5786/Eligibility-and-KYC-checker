"""
Agent 2 — Authenticity Verification
Checks whether the submitted document appears genuine.
"""

from agents.base_agent import BaseAgent


SYSTEM_PROMPT = """You are a Document Authenticity Verification Agent for an Indian financial institution.
Based on the customer data and document extraction results, assess whether the document is likely authentic.

Consider:
- Document number format validity for the given document type (Aadhaar = 12 digits, PAN = XXXXX9999X format, etc.)
- Consistency between name, DOB, and other fields
- Whether the document is expired
- Whether the uploaded file was provided (simulate confidence adjustment)
- Any red flags in the data

Respond ONLY with a valid JSON object:
- authenticity_score: integer 0-100 (100 = fully authentic)
- tamper_detected: boolean
- format_valid: boolean
- expiry_status: "VALID" | "EXPIRED" | "NOT_APPLICABLE"
- red_flags: list of strings
- verdict: "GENUINE" | "SUSPICIOUS" | "LIKELY_FAKE"
- summary: one sentence
"""


class AuthenticityAgent(BaseAgent):
    name = "authenticity_agent"

    def run(self, context: dict) -> dict:
        customer  = context["customer"]
        doc_data  = context.get("document_agent", {})

        user_prompt = f"""
Customer document type: {customer.get('doc_type')}
Document number: {customer.get('doc_number')}
Document expiry: {customer.get('doc_expiry')}
Document uploaded: {customer.get('has_id_doc')}
Extraction result: {doc_data.get('validation_status', 'N/A')}
Extraction issues: {doc_data.get('issues', [])}
Completeness score: {doc_data.get('completeness_score', 0)}

Assess authenticity and return JSON.
"""

        result = self.groq.chat_json(SYSTEM_PROMPT, user_prompt)
        result.setdefault("summary", f"Verdict: {result.get('verdict','N/A')} | Score: {result.get('authenticity_score',0)}")
        return result
