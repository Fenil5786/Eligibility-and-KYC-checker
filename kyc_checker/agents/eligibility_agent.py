"""
Agent 4 — Eligibility Check
Evaluates whether the customer meets product-specific eligibility criteria.
"""

from agents.base_agent import BaseAgent


SYSTEM_PROMPT = """You are an Eligibility Rules Engine Agent for an Indian financial institution.
Evaluate whether the customer meets the eligibility criteria for their chosen product.

Standard eligibility rules by product:
- Personal Loan: Age 21-60, Income >= ₹2.5L/yr, CIBIL >= 650, Employed/Self-Employed
- Home Loan: Age 21-65, Income >= ₹3L/yr, CIBIL >= 700, Stable employment
- Credit Card: Age 21-60, Income >= ₹1.8L/yr, CIBIL >= 650
- Savings Account: Age >= 18, Any nationality, No minimum income
- Fixed Deposit: Age >= 18, Any nationality, No minimum income
- Business Loan: Age 25-65, Income >= ₹5L/yr, CIBIL >= 680, Business Owner/Self-Employed
- Insurance: Age 18-65, No minimum income

Check against these rules and any geographic or other restrictions.

Respond ONLY with a valid JSON object:
- age_eligible: boolean
- income_eligible: boolean
- credit_score_eligible: boolean
- employment_eligible: boolean
- geography_eligible: boolean
- overall_eligibility: "ELIGIBLE" | "PARTIALLY_ELIGIBLE" | "NOT_ELIGIBLE"
- failed_criteria: list of strings
- passed_criteria: list of strings
- eligibility_score: integer 0-100
- summary: one sentence
"""


class EligibilityAgent(BaseAgent):
    name = "eligibility_agent"

    def run(self, context: dict) -> dict:
        customer = context["customer"]

        user_prompt = f"""
Product Applied For: {customer.get('product_type')}
Date of Birth: {customer.get('dob')}
Annual Income: ₹{customer.get('annual_income', 0):,}
Employment Type: {customer.get('employment')}
Credit Score (CIBIL): {customer.get('credit_score')}
State: {customer.get('state')}
Nationality: {customer.get('nationality')}
Existing Customer: {customer.get('existing_customer')}

Evaluate eligibility and return JSON.
"""

        result = self.groq.chat_json(SYSTEM_PROMPT, user_prompt)
        result.setdefault("summary", f"Eligibility: {result.get('overall_eligibility','N/A')} | Score: {result.get('eligibility_score',0)}")
        return result
