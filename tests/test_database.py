"""
Unit tests for database connection and SQLAlchemy models.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, UTC

from database.models import Base, User, Case, Document, Transaction, Authority, Communication, Task, Escalation, AuditLog

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_database_crud(test_db):
    # 1. Create User
    user = User(
        user_id="U-TEST-001",
        username="tester",
        email="tester@bankfreeze.ai",
        password_hash="mock_hash",
        role="COMPLIANCE_OFFICER"
    )
    test_db.add(user)
    test_db.commit()
    assert test_db.query(User).count() == 1

    # 2. Create Case
    case = Case(
        case_id="CASE-TEST-001",
        user_id=user.user_id,
        bank_name="Test Bank Ltd",
        masked_account_number="XXXX-XXXX-9999",
        freeze_date=datetime.now(UTC),
        restriction_type="DEBIT_FREEZE",
        freeze_reason="Test freeze reason",
        status="NEW"
    )
    test_db.add(case)
    test_db.commit()
    assert test_db.query(Case).count() == 1

    # 3. Create Document
    doc = Document(
        case_id=case.case_id,
        filename="notice.pdf",
        document_type="FREEZE_NOTICE",
        extracted_text="Notice content"
    )
    test_db.add(doc)
    test_db.commit()
    assert len(case.documents) == 1

    # 4. Create Transaction
    txn = Transaction(
        transaction_id="TXN-TEST-123",
        case_id=case.case_id,
        amount=15000.0,
        transaction_date=datetime.now(UTC),
        dispute_status="DISPUTED",
        source="TEST"
    )
    test_db.add(txn)
    test_db.commit()
    assert len(case.transactions) == 1

    # 5. Create Authority
    auth = Authority(
        case_id=case.case_id,
        authority_name="Cyber Cell Unit",
        jurisdiction="New Delhi",
        reference_number="REF-9988",
        source="DOC",
        confidence="HIGH"
    )
    test_db.add(auth)
    test_db.commit()
    assert len(case.authorities) == 1

    # 6. Create Communication
    comm = Communication(
        case_id=case.case_id,
        recipient_type="BANK",
        subject="Clarification",
        body="Body text",
        status="DRAFT"
    )
    test_db.add(comm)
    test_db.commit()
    assert len(case.communications) == 1

    # 7. Create Task & Escalation & Audit
    task = Task(case_id=case.case_id, title="Test Task", status="PENDING")
    esc = Escalation(case_id=case.case_id, level="LEVEL_1", reason="Awaiting response", channel="Branch")
    audit = AuditLog(case_id=case.case_id, actor="SYSTEM", action="INIT_TEST", result="SUCCESS")
    test_db.add_all([task, esc, audit])
    test_db.commit()

    assert len(case.tasks) == 1
    assert len(case.escalations) == 1
    assert len(case.audit_logs) == 1
