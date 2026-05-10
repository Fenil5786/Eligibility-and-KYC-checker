"""
Agent 1 — Document Extraction
Reads and validates submitted document data.
"""

from agents.base_agent import BaseAgent


SYSTEM_PROMPT = """You are a KYC Document Extraction Agent for an Indian financial institution.
Your job is to analyse the structured customer data provided and:
1. Extract all key fields (name, DOB, address, ID type & number, expiry).
2. Validate each field (format checks, completeness, logical consistency).
3. Flag any missing or suspicious values.

Respond ONLY with a valid JSON object with these keys:
- extracted_fields: dict of field -> value
- validation_status: "PASS" | "PARTIAL" | "FAIL"
- issues: list of strings describing any problems (empty list if none)
- completeness_score: integer 0-100
- summary: one sentence summary
"""


class DocumentExtractionAgent(BaseAgent):
    name = "document_agent"

    def run(self, context: dict) -> dict:
        customer = context["customer"]

        user_prompt = f"""
Extract and validate the following customer submission for KYC:

Full Name: {customer.get('full_name')}
Date of Birth: {customer.get('dob')}
Gender: {customer.get('gender')}
Nationality: {customer.get('nationality')}
Address: {customer.get('address')}
State: {customer.get('state')}
Document Type: {customer.get('doc_type')}
Document Number: {customer.get('doc_number')}
Document Expiry: {customer.get('doc_expiry')}
Has Uploaded ID Document: {customer.get('has_id_doc')}
Has Uploaded Selfie: {customer.get('has_selfie')}
Product Applied For: {customer.get('product_type')}

Validate all fields and return your analysis as JSON.
"""

        result = self.groq.chat_json(SYSTEM_PROMPT, user_prompt)
        result.setdefault("summary", f"Extracted {len(result.get('extracted_fields', {}))} fields. Status: {result.get('validation_status','N/A')}")
        return result
