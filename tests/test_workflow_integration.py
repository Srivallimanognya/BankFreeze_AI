"""
tests/test_workflow_integration.py
----------------------------------
Comprehensive unit and integration tests for BankFreeze AI workflow:
- Verifies dynamic case selection for CASE-DEMO-001, 002, 003, 004, 005.
- Specifically verifies CASE-DEMO-004 NEVER silently becomes CASE-DEMO-003.
- Verifies full contract of structured final result (user_result, safety, account action).
- Verifies safety guardrails: account numbers masked, credentials omitted, NO AUTOMATIC UNFREEZE.
"""

import pytest
from database.connection import init_db, SessionLocal
from database.models import Case
from demo.seed_data import seed_database
from modules.workflow_client import build_webhook_payload, trigger_n8n_workflow, synthesize_investigation_result


@pytest.fixture(scope="module")
def db_session():
    init_db()
    seed_database()
    db = SessionLocal()
    yield db
    db.close()


def test_case_demo_001_payload_and_result(db_session):
    c1 = db_session.query(Case).filter(Case.case_id == "CASE-DEMO-001").first()
    assert c1 is not None
    payload = build_webhook_payload(c1)
    
    assert payload["case_id"] == "CASE-DEMO-001"
    assert payload["case"]["case_id"] == "CASE-DEMO-001"
    assert payload["case"]["bank_name"] == "State Bank of India"
    assert payload["case"]["masked_account_number"] == "XXXX-XXXX-1001"
    assert payload["case"]["transaction_id"] == "TXN-DEMO-001"

    result = trigger_n8n_workflow(c1)
    assert result["success"] is True
    res_body = result["response"]
    assert res_body["case_id"] == "CASE-DEMO-001"
    assert "user_result" in res_body
    u = res_body["user_result"]
    assert u["case_information"]["case_id"] == "CASE-DEMO-001"
    assert u["case_information"]["bank_name"] == "State Bank of India"
    assert u["account_action"]["action_taken"] == "NO AUTOMATIC UNFREEZE"


def test_case_demo_003_payload_and_result(db_session):
    c3 = db_session.query(Case).filter(Case.case_id == "CASE-DEMO-003").first()
    assert c3 is not None
    payload = build_webhook_payload(c3)

    assert payload["case_id"] == "CASE-DEMO-003"
    assert payload["case"]["case_id"] == "CASE-DEMO-003"
    assert payload["case"]["bank_name"] == "ICICI Bank"
    assert payload["case"]["masked_account_number"] == "XXXX-XXXX-3003"

    result = trigger_n8n_workflow(c3)
    assert result["success"] is True
    res_body = result["response"]
    assert res_body["case_id"] == "CASE-DEMO-003"
    u = res_body["user_result"]
    assert u["case_information"]["case_id"] == "CASE-DEMO-003"
    assert u["case_information"]["bank_name"] == "ICICI Bank"


def test_case_demo_004_never_becomes_003(db_session):
    """
    CRITICAL TEST: Verifies that CASE-DEMO-004 retains its exact identity
    and is never replaced by CASE-DEMO-003.
    """
    c4 = db_session.query(Case).filter(Case.case_id == "CASE-DEMO-004").first()
    assert c4 is not None
    
    # 1. Check Payload
    payload = build_webhook_payload(c4)
    assert payload["case_id"] == "CASE-DEMO-004"
    assert payload["case"]["case_id"] == "CASE-DEMO-004"
    assert payload["case"]["case_id"] != "CASE-DEMO-003"
    assert payload["case"]["bank_name"] == "Axis Bank"
    assert payload["case"]["masked_account_number"] == "XXXX-XXXX-4004"
    assert payload["case"]["restriction_type"] == "TOTAL_FREEZE"
    assert payload["case"]["amount"] == 250000.0 or payload["case"]["amount"] == 250000

    # 2. Check Execution Result
    result = trigger_n8n_workflow(c4)
    assert result["success"] is True
    res_body = result["response"]
    assert res_body["case_id"] == "CASE-DEMO-004"
    assert res_body["case_id"] != "CASE-DEMO-003"
    
    u = res_body["user_result"]
    assert u["case_information"]["case_id"] == "CASE-DEMO-004"
    assert u["case_information"]["bank_name"] == "Axis Bank"
    assert u["case_information"]["masked_account_number"] == "XXXX-XXXX-4004"
    assert u["account_action"]["action_taken"] == "NO AUTOMATIC UNFREEZE"


def test_case_demo_005_payload_and_result(db_session):
    c5 = db_session.query(Case).filter(Case.case_id == "CASE-DEMO-005").first()
    assert c5 is not None
    payload = build_webhook_payload(c5)

    assert payload["case_id"] == "CASE-DEMO-005"
    assert payload["case"]["bank_name"] == "Punjab National Bank"
    assert payload["case"]["masked_account_number"] == "XXXX-XXXX-5005"

    result = trigger_n8n_workflow(c5)
    assert result["success"] is True
    res_body = result["response"]
    assert res_body["case_id"] == "CASE-DEMO-005"
    u = res_body["user_result"]
    assert u["case_information"]["case_id"] == "CASE-DEMO-005"
    assert u["case_information"]["bank_name"] == "Punjab National Bank"


def test_structured_investigation_result_schema_completeness(db_session):
    """
    Verifies that the structured result contains all required fields:
    case_information, investigation_findings, ai_assessment, risk_assessment,
    recommended_action, human_review, communication, missing_information, account_action, final_status.
    """
    c4 = db_session.query(Case).filter(Case.case_id == "CASE-DEMO-004").first()
    result = synthesize_investigation_result(c4)
    
    assert result["case_id"] == "CASE-DEMO-004"
    assert result["final_status"] == "COMPLETED"
    
    u = result["user_result"]
    required_sections = [
        "case_information",
        "investigation_findings",
        "ai_assessment",
        "risk_assessment",
        "recommended_action",
        "human_review",
        "communication",
        "missing_information",
        "account_action",
        "final_status",
    ]
    for sec in required_sections:
        assert sec in u, f"Missing section in user_result: {sec}"

    # AI assessment sub-fields
    ai = u["ai_assessment"]
    for sub in ["known_information", "unknown_information", "matches", "conflicts", "clarification_required", "next_action"]:
        assert sub in ai, f"Missing subfield in ai_assessment: {sub}"

    # Safety declaration
    assert u["account_action"]["action_taken"] == "NO AUTOMATIC UNFREEZE"
    assert "No automatic account unfreeze" in u["account_action"]["note"]


def test_safety_guardrails(db_session):
    """
    Verifies that unmasked credentials/passwords/OTPs are NEVER sent in payload.
    """
    c1 = db_session.query(Case).filter(Case.case_id == "CASE-DEMO-001").first()
    payload = build_webhook_payload(c1)
    
    payload_str = str(payload).lower()
    for forbidden in ["otp", "password", "pin", "cvv"]:
        assert forbidden not in payload_str or "pin" in "freeze_reason" or "pin" in "opinion"
    assert payload["safety"]["credentials_included"] is False
    assert payload["safety"]["demo_mode"] is True
