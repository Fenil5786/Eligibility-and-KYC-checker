"""
Agent 3 — Face Match & Document Verification
Supports multiple document types and autonomous actions.
"""

from agents.base_agent import BaseAgent
from utils.aadhar_extractor import extract_document_details, compare_document_with_submission
from utils.agent_tools import validate_doc_number_format, create_manual_review_ticket, log_agent_action


FACE_MATCHING_PROMPT = """You are a Biometric Face Verification Agent for KYC.
Analyze the face matching results between document photo and selfie:

{face_comparison_data}

Also consider:
- Document data match with submitted details: {document_match_result}
- Quality of photos: {quality_data}

Provide a comprehensive assessment:
- face_match_score: 0-100 (percentage match between Aadhar and selfie)
- data_match_score: 0-100 (Document data vs submitted data)
- liveness_check: "PASS" | "FAIL" | "UNCERTAIN"
- overall_verdict: "MATCH" | "MISMATCH" | "INCONCLUSIVE"
- confidence_level: "HIGH" | "MEDIUM" | "LOW"
- risk_flags: list of issues found
- summary: brief assessment

Respond ONLY with valid JSON."""


class FaceMatchAgent(BaseAgent):
    name = "face_match_agent"

    def run(self, context: dict) -> dict:
        customer = context["customer"]
        auth = context.get("authenticity_agent", {})
        correlation_id = context.get("meta", {}).get("correlation_id", "NA")

        # Get file paths if available
        doc_file_path = customer.get("doc_file_path") or customer.get("aadhar_file_path")
        selfie_file_path = customer.get("selfie_file_path")
        doc_type = customer.get("doc_type", "Aadhaar Card")

        document_data = {}
        data_match_result = {}
        face_match_score = 0
        mismatches = []
        actions = []

        format_check = validate_doc_number_format(doc_type, customer.get("doc_number", ""))
        actions.append(format_check)
        if not format_check.get("valid"):
            mismatches.append(f"{doc_type} number format invalid")

        # Step 1: Extract document details if file is available
        if doc_file_path:
            try:
                extraction_result = extract_document_details(doc_file_path, doc_type, self.groq)
                if extraction_result.get("status") == "success":
                    document_data = extraction_result.get("extracted_fields", {})
                    
                    # Step 2: Compare extracted document data with submitted data
                    submitted_data = {
                        "full_name": customer.get("full_name", ""),
                        "date_of_birth": customer.get("dob", ""),
                        "gender": customer.get("gender", ""),
                        "address": customer.get("address", ""),
                        "doc_number": customer.get("doc_number", ""),
                        "state": customer.get("state", "")
                    }
                    
                    data_match_result = compare_document_with_submission(document_data, submitted_data, doc_type)
                    face_match_score = data_match_result.get("match_score", 0)
                    mismatches = data_match_result.get("mismatches", [])
                else:
                    mismatches.append(f"Document extraction failed: {extraction_result.get('error', 'Unknown error')}")
            except Exception as e:
                mismatches.append(f"Document verification error: {str(e)}")

        # Step 3: Generate comprehensive face match result
        user_prompt = f"""
Aadhaar or ID Data Extracted: {bool(document_data)}
Document Match Score: {face_match_score}
Document Mismatches: {mismatches}
Data Match Verdict: {data_match_result.get('verdict', 'UNKNOWN')}

Selfie uploaded: {customer.get('has_selfie')}
ID document uploaded: {customer.get('has_id_doc')}
Selfie file path present: {bool(selfie_file_path)}
Document authenticity verdict: {auth.get('verdict', 'N/A')}
Document authenticity score: {auth.get('authenticity_score', 0)}

Key mismatches found in document comparison:
{chr(10).join([f'- {m}' for m in mismatches]) if mismatches else '- No critical mismatches'}

Based on the document data extraction and comparison, provide face match assessment.
If there are mismatches in critical fields like name, DOB, or document number, the verdict should be MISMATCH.
"""

        result = self.groq.chat_json(FACE_MATCHING_PROMPT, user_prompt)
        
        # Add detailed comparison data to result
        result["document_type"] = doc_type
        result["document_extracted"] = document_data
        result["data_comparison"] = data_match_result.get("field_comparisons", {})
        result["mismatches"] = mismatches
        result["document_match_verdict"] = data_match_result.get("verdict", "UNKNOWN")

        # Autonomous action: create manual review ticket on critical mismatch.
        if mismatches and len(mismatches) > 1:
            result["overall_verdict"] = "MISMATCH"
            result["face_match_score"] = min(result.get("face_match_score", 0), 30)
            result["confidence_level"] = "LOW"
            ticket = create_manual_review_ticket(
                customer=customer,
                mismatches=mismatches,
                reason="Critical KYC mismatch detected by autonomous agent",
            )
            actions.append(ticket)

        action_log = log_agent_action(
            correlation_id=correlation_id,
            agent_name=self.name,
            action="face_and_document_verification_completed",
            details={"mismatch_count": len(mismatches), "doc_type": doc_type},
        )
        actions.append(action_log)

        result.setdefault("summary", 
            f"Face match: {result.get('overall_verdict','N/A')} | "
            f"Document Data: {result.get('document_match_verdict','N/A')} | "
            f"Confidence: {result.get('confidence_level','UNKNOWN')}")
        result["autonomous_actions"] = actions

        return result
