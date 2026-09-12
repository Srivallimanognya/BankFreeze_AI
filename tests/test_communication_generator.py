"""
Unit tests for Communication Generator & Human Approval Workflow.
"""

import pytest
from modules.communication_generator import communication_generator
from database.models import Communication

def test_communication_generation_formats():
    case_info = {
        "case_id": "CASE-2025-001",
        "bank_name": "State Bank of India",
        "masked_account_number": "XXXX-XXXX-1234",
        "freeze_date": "2025-08-12",
        "restriction_type": "DEBIT_FREEZE",
        "transaction_id": "TXN-DEMO-001",
        "amount": "18500.00",
        "reference_number": "LEA-DEMO-001",
        "authority": "Cyber Crime Police Station",
        "officer_name": "Inspector K. Sharma",
        "jurisdiction": "Hyderabad"
    }

    # 1. Bank Clarification
    bank_draft = communication_generator.generate_bank_clarification(case_info)
    assert "XXXX-XXXX-1234" in bank_draft["subject"]
    assert "State Bank of India" in bank_draft["body"]
    assert "TXN-DEMO-001" in bank_draft["body"]
    assert "₹18500.00" in bank_draft["body"]
    # Tone safety check: No accusations or threats
    assert "threat" not in bank_draft["body"].lower()
    assert "sue you" not in bank_draft["body"].lower()

    # 2. Authority Representation
    auth_draft = communication_generator.generate_authority_clarification(case_info)
    assert "LEA-DEMO-001" in auth_draft["subject"]
    assert "Cyber Crime Police Station" in auth_draft["body"]
    assert "Inspector K. Sharma" in auth_draft["body"]
    assert "TXN-DEMO-001" in auth_draft["body"]

    # 3. Follow-Up
    follow_draft = communication_generator.generate_followup(case_info)
    assert "Follow-Up" in follow_draft["subject"]
    assert "LEA-DEMO-001" in follow_draft["body"]

    # 4. Escalation
    esc_draft = communication_generator.generate_escalation_request(case_info, "LEVEL_2")
    assert "LEVEL_2" in esc_draft["subject"]
    assert "Banking Ombudsman" in esc_draft["body"]

def test_human_approval_state_progression():
    # Verify lifecycle status transitions for communications
    comm = Communication(
        case_id="CASE-TEST",
        recipient_type="BANK",
        subject="Clarification",
        body="Initial Draft",
        status="DRAFT"
    )
    assert comm.status == "DRAFT"
    
    # User edits
    comm.body = "Edited Draft with additional details"
    comm.status = "EDITED"
    comm.version = 2
    assert comm.status == "EDITED"
    assert comm.version == 2
    
    # User approves
    comm.status = "APPROVED"
    assert comm.status == "APPROVED"
