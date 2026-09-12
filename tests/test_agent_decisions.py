"""
Unit tests for Resolution Agent Tools and Decision Synthesis.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, UTC

from database.models import Base, User, Case, Transaction, Authority, Task
from modules.resolution_agent import ResolutionAgent
from schemas.case import CaseStatus

@pytest.fixture
def agent_test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    db = TestingSession()

    user = User(user_id="U-AGENT", username="agent_user", email="agent@test.com", password_hash="hash")
    db.add(user)
    db.commit()

    case = Case(
        case_id="CASE-DEMO-001",
        user_id="U-AGENT",
        bank_name="State Bank of India",
        masked_account_number="XXXX-XXXX-1001",
        freeze_date=datetime.now(UTC),
        restriction_type="DEBIT_FREEZE",
        freeze_reason="P2P Transfer Flagged",
        status="NEW"
    )
    txn = Transaction(
        transaction_id="TXN-DEMO-001",
        case_id="CASE-DEMO-001",
        amount=18500.0,
        transaction_date=datetime.now(UTC),
        dispute_status="DISPUTED",
        source="BANK"
    )
    auth = Authority(
        case_id="CASE-DEMO-001",
        authority_name="Cyber Crime Police Station",
        jurisdiction="Hyderabad",
        reference_number="LEA-DEMO-001",
        source="NOTICE",
        confidence="HIGH"
    )
    db.add_all([case, txn, auth])
    db.commit()

    try:
        yield db
    finally:
        db.close()

def test_agent_tools_execution(agent_test_db):
    agent = ResolutionAgent(agent_test_db)
    
    # 1. get_case
    c = agent.get_case("CASE-DEMO-001")
    assert c is not None
    assert c.bank_name == "State Bank of India"
    
    # 2. get_bank_information
    bank_data = agent.get_bank_information("CASE-DEMO-001")
    assert bank_data.get("status") == "RESTRICTED"
    assert bank_data.get("transaction_id") == "TXN-DEMO-001"
    
    # 3. get_authority_information
    auth_data = agent.get_authority_information("CASE-DEMO-001")
    assert auth_data.get("found") is True
    assert auth_data.get("authority_name") == "Cyber Crime Police Station"
    
    # 4. create_task
    t = agent.create_task("CASE-DEMO-001", "Verify Trade Invoice", "Check buyer details")
    assert t.title == "Verify Trade Invoice"
    assert agent_test_db.query(Task).count() == 1
    
    # 5. update_case_status
    c_updated = agent.update_case_status("CASE-DEMO-001", CaseStatus.CASE_ANALYSIS)
    assert c_updated.status == CaseStatus.CASE_ANALYSIS.value

def test_agent_reasoning_and_safety_guardrails(agent_test_db):
    agent = ResolutionAgent(agent_test_db)
    reasoning = agent.reason_and_synthesize("CASE-DEMO-001")
    
    # Check reasoning outputs
    assert len(reasoning["knowns"]) > 0
    assert "guardrail_notice" in reasoning
    
    # Verify safety rule: Agent NEVER promises account can be unfrozen
    all_recs = " ".join(reasoning["recommended_actions"]).lower()
    assert "account will be unfrozen" not in all_recs
    assert "guarantee unfreeze" not in all_recs
    
    # Contact targets must be populated
    assert len(reasoning["contact_targets"]) >= 1
