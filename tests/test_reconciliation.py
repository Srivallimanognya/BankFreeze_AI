"""
Unit tests for Multi-Source Reconciliation & Mismatch Detection.
"""

import pytest
from modules.reconciliation import reconciler
from schemas.reconciliation import ReconciliationStatus

def test_reconciliation_match():
    user_info = {"transaction_id": "TXN-DEMO-001", "amount": "18500", "reference_number": "LEA-DEMO-001"}
    bank_details = {"transaction_id": "TXN-DEMO-001", "amount": 18500.0, "reference_number": "LEA-DEMO-001"}
    auth_details = {"transaction_id": "TXN-DEMO-001", "disputed_amount": 18500.0, "reference_number": "LEA-DEMO-001"}

    res = reconciler.reconcile_case("CASE-TEST", user_info, None, bank_details, auth_details)
    
    assert res.has_critical_conflicts is False
    assert res.can_proceed_to_resolution is True
    
    # Check amount comparison status
    amt_comp = next(c for c in res.comparisons if c.field_name == "Disputed Amount")
    assert amt_comp.status == ReconciliationStatus.MATCH

def test_reconciliation_critical_mismatch():
    # As requested in user specifications:
    # BANK: TXN-DEMO-001 / ₹18,500
    # AUTHORITY: TXN-DEMO-002 / ₹25,000 -> MISMATCH
    user_info = {"transaction_id": "TXN-DEMO-001", "amount": "18500"}
    bank_details = {"transaction_id": "TXN-DEMO-001", "amount": 18500.0}
    auth_details = {"transaction_id": "TXN-DEMO-002", "disputed_amount": 25000.0}

    res = reconciler.reconcile_case("CASE-CONFLICT", user_info, None, bank_details, auth_details)
    
    assert res.has_critical_conflicts is True
    assert res.can_proceed_to_resolution is False
    assert len(res.conflict_summary) >= 2  # Amount and Transaction ID both mismatch
    assert res.overall_status == "CONFLICT_DETECTED"

def test_reconciliation_missing_information():
    user_info = {}
    bank_details = {}
    auth_details = {}

    res = reconciler.reconcile_case("CASE-EMPTY", user_info, None, bank_details, auth_details)
    
    for comp in res.comparisons:
        assert comp.status == ReconciliationStatus.MISSING
    assert res.has_critical_conflicts is False
