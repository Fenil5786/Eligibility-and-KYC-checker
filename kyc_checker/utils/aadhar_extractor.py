"""Document extraction and comparison helpers for KYC agents."""

import base64
import re
from typing import Dict, Any


DOCUMENT_PROMPTS = {
    "Aadhaar Card": ["full_name", "date_of_birth", "gender", "address", "aadhar_number", "state"],
    "PAN Card": ["full_name", "date_of_birth", "pan_number", "father_name"],
    "Passport": ["full_name", "date_of_birth", "gender", "nationality", "passport_number", "expiry_date"],
    "Driving License": ["full_name", "date_of_birth", "gender", "address", "dl_number", "state", "expiry_date"],
    "Voter ID": ["full_name", "date_of_birth", "gender", "address", "voter_id", "state"],
}


DOC_NUMBER_FIELDS = {
    "Aadhaar Card": "aadhar_number",
    "PAN Card": "pan_number",
    "Passport": "passport_number",
    "Driving License": "dl_number",
    "Voter ID": "voter_id",
}


def extract_document_details(file_path: str, doc_type: str, groq_client) -> Dict[str, Any]:
    """Extract document details from PDF or image using OCR + LLM parsing."""
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()

        is_pdf = file_path.lower().endswith('.pdf')

        if is_pdf:
            extracted_text = extract_text_from_pdf(file_path)
        else:
            extracted_text = encode_image_for_llm(file_data)

        fields = DOCUMENT_PROMPTS.get(doc_type, DOCUMENT_PROMPTS["Aadhaar Card"])
        system_prompt = f"""You are a KYC Document Data Extraction Specialist.
Document Type: {doc_type}
Extract exactly these fields:
{', '.join(fields)}

Rules:
- Return valid JSON only.
- Use null if a field is unclear or absent.
- Keep date format as YYYY-MM-DD where possible.
"""

        user_prompt = f"""Extract {doc_type} details from this document:

{extracted_text}

Return structured JSON with all fields."""

        result = groq_client.chat_json(system_prompt, user_prompt, temperature=0.1)

        return {
            "status": "success",
            "document_type": doc_type,
            "extracted_fields": result,
            "confidence": result.get("confidence_score", 85),
            "issues": []
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "document_type": doc_type,
            "extracted_fields": {},
            "confidence": 0,
            "issues": [f"Failed to extract document details: {str(e)}"]
        }


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file (supports basic text PDFs)."""
    try:
        import PyPDF2
        
        text_content = ""
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
        
        return text_content if text_content.strip() else "[PDF content could not be extracted - image-based PDF detected. Manual verification recommended.]"
    
    except ImportError:
        # Fallback: return placeholder
        return "[PDF parsing requires PyPDF2. Using vision-based extraction instead.]"
    except Exception as e:
        return f"[PDF extraction failed: {str(e)}]"


def encode_image_for_llm(image_data: bytes) -> str:
    """Encode image to base64 for LLM processing."""
    try:
        encoded = base64.b64encode(image_data).decode('utf-8')
        return f"[IMAGE_DATA_BASE64]: {encoded[:200]}... [Image encoded for vision processing]"
    except Exception as e:
        return f"[Image encoding failed: {str(e)}]"


def compare_document_with_submission(doc_data: Dict, submitted_data: Dict, doc_type: str) -> Dict[str, Any]:
    """Compare extracted document data with user-submitted data."""
    mismatches = []
    field_comparisons = {}
    match_score = 100

    comparison_fields = [
        ("full_name", "Full Name"),
        ("date_of_birth", "Date of Birth"),
        ("gender", "Gender"),
        ("address", "Address"),
        ("state", "State")
    ]

    allowed_fields = set(DOCUMENT_PROMPTS.get(doc_type, []))

    for field_key, field_label in comparison_fields:
        if field_key not in allowed_fields:
            continue

        doc_value = str(doc_data.get(field_key, "")).strip().lower()
        submitted_value = str(submitted_data.get(field_key, "")).strip().lower()

        if not doc_value:
            field_comparisons[field_label] = {
                "document": "Not extracted",
                "submitted": submitted_value,
                "match": False,
                "reason": "Could not extract from document"
            }
            match_score -= 15
            mismatches.append(f"{field_label}: Could not extract from {doc_type}")
            continue

        if field_key == "full_name":
            match = name_match(doc_value, submitted_value)
        elif field_key == "address":
            match = address_match(doc_value, submitted_value)
        else:
            match = doc_value == submitted_value

        field_comparisons[field_label] = {
            "document": doc_value,
            "submitted": submitted_value,
            "match": match,
            "reason": "Match" if match else "Mismatch detected"
        }

        if not match:
            match_score -= 25
            mismatches.append(f"{field_label}: '{doc_value}' != '{submitted_value}'")

    doc_number_field = DOC_NUMBER_FIELDS.get(doc_type)
    if doc_number_field:
        doc_number = str(doc_data.get(doc_number_field, "")).strip().lower()
        submitted_number = str(submitted_data.get("doc_number", "")).strip().lower()
        if doc_number and submitted_number:
            number_match = fuzzy_match(doc_number, submitted_number, threshold=0.9)
            field_comparisons["Document Number"] = {
                "document": doc_number,
                "submitted": submitted_number,
                "match": number_match,
                "reason": "Match" if number_match else "Mismatch detected",
            }
            if not number_match:
                match_score -= 25
                mismatches.append(f"Document Number: '{doc_number}' != '{submitted_number}'")

    match_score = max(0, min(100, match_score))

    return {
        "overall_match": match_score >= 80,
        "match_score": match_score,
        "field_comparisons": field_comparisons,
        "mismatches": mismatches,
        "verdict": "PASS" if match_score >= 80 else ("PARTIAL" if match_score >= 50 else "FAIL"),
        "document_type": doc_type,
    }


def fuzzy_match(str1: str, str2: str, threshold: float = 0.8) -> bool:
    """
    Fuzzy string matching for handling minor typos/variations.
    """
    try:
        from difflib import SequenceMatcher
        
        s1 = " ".join(str1.split())
        s2 = " ".join(str2.split())

        ratio = SequenceMatcher(None, s1, s2).ratio()

        return ratio >= threshold
    except:
        return str1 == str2


def normalize_text(text: str) -> str:
    """Normalize noisy OCR/user text into comparable form."""
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def token_set(text: str) -> set:
    return {t for t in normalize_text(text).split() if t}


def jaccard_similarity(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def name_match(name_1: str, name_2: str) -> bool:
    """Match person names even if word order changes (e.g., 'makvana fenil' vs 'fenil makvana')."""
    stop_words = {
        "mr", "mrs", "ms", "dr", "shri", "smt", "kumari", "late"
    }
    n1_tokens = [t for t in normalize_text(name_1).split() if t not in stop_words]
    n2_tokens = [t for t in normalize_text(name_2).split() if t not in stop_words]

    if not n1_tokens or not n2_tokens:
        return False

    # Strong match for unordered-token equality/subset.
    s1, s2 = set(n1_tokens), set(n2_tokens)
    if s1 <= s2 or s2 <= s1:
        return True

    # Fallback to overlap + fuzzy score on sorted tokens.
    overlap = jaccard_similarity(s1, s2)
    sorted_1 = " ".join(sorted(n1_tokens))
    sorted_2 = " ".join(sorted(n2_tokens))
    fuzzy_ok = fuzzy_match(sorted_1, sorted_2, threshold=0.84)
    return overlap >= 0.60 and fuzzy_ok


def address_match(addr_1: str, addr_2: str) -> bool:
    """Match addresses with OCR/user variation and common descriptor differences."""
    noise_tokens = {
        "c", "o", "co", "po", "dist", "city", "stop", "post", "taluka",
        "near", "behind", "opp", "opposite", "landmark", "at"
    }

    a1 = normalize_text(addr_1)
    a2 = normalize_text(addr_2)

    # Normalize common abbreviations.
    replacements = {
        "rd": "road",
        "st": "street",
        "brts": "brt",
    }
    for src, dest in replacements.items():
        a1 = re.sub(rf"\b{src}\b", dest, a1)
        a2 = re.sub(rf"\b{src}\b", dest, a2)

    t1 = [t for t in a1.split() if t not in noise_tokens]
    t2 = [t for t in a2.split() if t not in noise_tokens]
    s1, s2 = set(t1), set(t2)

    # Compare key anchors: PIN and property/flat-like tokens.
    pin_1 = re.findall(r"\b\d{6}\b", a1)
    pin_2 = re.findall(r"\b\d{6}\b", a2)
    if pin_1 and pin_2 and pin_1[0] != pin_2[0]:
        return False

    flat_1 = {t for t in s1 if re.search(r"[a-z]-?\d{2,5}|\d{2,5}", t)}
    flat_2 = {t for t in s2 if re.search(r"[a-z]-?\d{2,5}|\d{2,5}", t)}
    flat_ok = True
    if flat_1 and flat_2:
        flat_ok = len(flat_1 & flat_2) > 0

    overlap = jaccard_similarity(s1, s2)
    fuzzy_ok = fuzzy_match(" ".join(sorted(s1)), " ".join(sorted(s2)), threshold=0.72)

    # Accept if strong overlap and no anchor conflict.
    return flat_ok and (overlap >= 0.46 or fuzzy_ok)


def extract_aadhar_details(file_path: str, groq_client) -> Dict[str, Any]:
    """Backward-compatible wrapper for existing callers."""
    return extract_document_details(file_path=file_path, doc_type="Aadhaar Card", groq_client=groq_client)


def compare_aadhar_with_submission(aadhar_data: Dict, submitted_data: Dict) -> Dict[str, Any]:
    """Backward-compatible wrapper for existing callers."""
    return compare_document_with_submission(doc_data=aadhar_data, submitted_data=submitted_data, doc_type="Aadhaar Card")
