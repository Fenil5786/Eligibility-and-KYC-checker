"""Autonomous tools for enterprise-grade agent actions."""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


DOC_NUMBER_PATTERNS = {
    "Aadhaar Card": r"^\d{4}\s?\d{4}\s?\d{4}$",
    "PAN Card": r"^[A-Z]{5}[0-9]{4}[A-Z]$",
    "Passport": r"^[A-Z][0-9]{7}$",
    "Driving License": r"^[A-Z]{2}[0-9]{2}[0-9]{11,13}$",
    "Voter ID": r"^[A-Z]{3}[0-9]{7}$",
}


def validate_doc_number_format(doc_type: str, doc_number: str) -> Dict[str, Any]:
    """Validate document number format using document-specific rules."""
    import re

    pattern = DOC_NUMBER_PATTERNS.get(doc_type)
    normalized = (doc_number or "").strip().upper()

    if not pattern:
        return {
            "tool": "validate_doc_number_format",
            "valid": False,
            "reason": f"No validator configured for {doc_type}",
            "normalized": normalized,
        }

    valid = re.match(pattern, normalized) is not None
    return {
        "tool": "validate_doc_number_format",
        "valid": valid,
        "reason": "format_ok" if valid else "format_invalid",
        "normalized": normalized,
    }


def create_manual_review_ticket(customer: Dict[str, Any], mismatches: list[str], reason: str) -> Dict[str, Any]:
    """Autonomous action: create a manual review ticket payload for operations."""
    ticket = {
        "ticket_id": f"KYC-REVIEW-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "customer_name": customer.get("full_name", "Unknown"),
        "doc_type": customer.get("doc_type", "Unknown"),
        "doc_number": customer.get("doc_number", "Unknown"),
        "reason": reason,
        "mismatches": mismatches,
        "status": "OPEN",
        "priority": "HIGH" if mismatches else "MEDIUM",
    }

    out_dir = Path(tempfile.gettempdir()) / "kyc_autonomous_actions"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{ticket['ticket_id']}.json"
    out_file.write_text(json.dumps(ticket, indent=2), encoding="utf-8")

    return {
        "tool": "create_manual_review_ticket",
        "created": True,
        "ticket": ticket,
        "ticket_path": str(out_file),
    }


def log_agent_action(correlation_id: str, agent_name: str, action: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """Autonomous action: write immutable-style action trail to temp storage."""
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "correlation_id": correlation_id,
        "agent": agent_name,
        "action": action,
        "details": details,
    }

    out_dir = Path(tempfile.gettempdir()) / "kyc_agent_action_logs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{correlation_id}.jsonl"
    with out_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    return {
        "tool": "log_agent_action",
        "logged": True,
        "log_path": str(out_file),
    }
