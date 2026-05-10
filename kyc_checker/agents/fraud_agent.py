"""
Agent 5 — Fraud & Sanctions Screening
Screens the customer against simulated fraud and sanctions watchlists.
"""

from agents.base_agent import BaseAgent


SYSTEM_PROMPT = """You are a Fraud Detection and Sanctions Screening Agent for a KYC system.
Simulate screening the customer against:
- RBI defaulter list
- SEBI debarred list
- OFAC sanctions list
- Interpol watchlist
- Internal fraud blacklist
- PEP (Politically Exposed Person) register
- Adverse media database

Use all available customer signals to assign risk.

Respond ONLY with a valid JSON object:
- pep_confirmed: boolean
- sanctions_hit: boolean
- fraud_history_flag: boolean
- adverse_media: boolean
- risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
- risk_score: integer 0-100
- watchlist_matches: list of strings (empty if none)
- screening_passed: boolean
- summary: one sentence
"""


class FraudSanctionsAgent(BaseAgent):
    name = "fraud_agent"

    def run(self, context: dict) -> dict:
        customer    = context["customer"]
        eligibility = context.get("eligibility_agent", {})

        user_prompt = f"""
Customer Name: {customer.get('full_name')}
Date of Birth: {customer.get('dob')}
Nationality: {customer.get('nationality')}
State: {customer.get('state')}
PEP Status (self-declared): {customer.get('pep_status')}
Employment: {customer.get('employment')}
Annual Income: ₹{customer.get('annual_income', 0):,}
Credit Score: {customer.get('credit_score')}
Existing Customer: {customer.get('existing_customer')}
Eligibility Score: {eligibility.get('eligibility_score', 0)}

Simulate watchlist screening and fraud risk assessment. Return JSON.
"""

        result = self.groq.chat_json(SYSTEM_PROMPT, user_prompt)
        result.setdefault("summary", f"Risk Level: {result.get('risk_level','N/A')} | Screening: {'PASSED' if result.get('screening_passed') else 'FAILED'}")
        return result
