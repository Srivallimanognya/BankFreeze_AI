"""
Unit tests for Case Lifecycle States and Transitions.
"""

import pytest
from schemas.case import CaseStatus, RestrictionType, CaseCreate
from modules.security import mask_account_number

def test_case_lifecycle_enum_complete():
    # Verify all 15 states exist
    required_states = [
        "NEW", "BANK_VERIFICATION", "AUTHORITY_IDENTIFICATION",
        "AUTHORITY_INQUIRY_REQUIRED", "WAITING_FOR_INFORMATION", "INFORMATION_RECEIVED",
        "CASE_ANALYSIS", "ACTION_REQUIRED", "USER_REVIEW", "APPROVED",
        "COMMUNICATION_RECORDED", "FOLLOW_UP_REQUIRED", "ESCALATION_REQUIRED",
        "RESOLVED", "CLOSED"
    ]
    for state in required_states:
        assert state in CaseStatus.__members__
    assert len(CaseStatus) == 15

def test_case_creation_schema():
    data = {
        "bank_name": "State Bank of India",
        "account_number": "123456789012",
        "restriction_type": RestrictionType.DEBIT_FREEZE,
        "freeze_reason": "Police investigation requisition",
        "disputed_amount": 18500.0,
        "transaction_id": "TXN-001"
    }
    case_create = CaseCreate(**data)
    assert case_create.bank_name == "State Bank of India"
    assert case_create.restriction_type == RestrictionType.DEBIT_FREEZE
    assert case_create.disputed_amount == 18500.0

def test_masked_account_creation():
    raw = "987654321098"
    masked = mask_account_number(raw)
    assert masked == "XXXX-XXXX-1098"
    assert not masked.startswith("9876")
