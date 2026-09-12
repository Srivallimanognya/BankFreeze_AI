"""
SQLAlchemy ORM Models for BankFreeze AI
Covers: users, cases, documents, transactions, authorities, communications, tasks, escalations, audit_logs.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, DateTime, Text, Integer, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def utc_now():
    return datetime.now(timezone.utc)

def generate_uuid() -> str:
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(64), primary_key=True, default=generate_uuid)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="USER", nullable=False)  # USER, COMPLIANCE_OFFICER, ADMIN
    created_at = Column(DateTime, default=utc_now, nullable=False)

    cases = relationship("Case", back_populates="user", cascade="all, delete-orphan")

class Case(Base):
    __tablename__ = "cases"

    case_id = Column(String(64), primary_key=True)  # e.g., CASE-DEMO-001 or CASE-2025-XXXX
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    bank_name = Column(String(150), nullable=False)
    masked_account_number = Column(String(50), nullable=False)
    freeze_date = Column(DateTime, default=utc_now, nullable=False)
    restriction_type = Column(String(100), nullable=False)  # DEBIT_FREEZE, TOTAL_FREEZE, LIEN_AMOUNT, etc.
    freeze_reason = Column(String(255), nullable=False)     # Stated freeze reason
    status = Column(String(64), default="NEW", nullable=False, index=True)  # One of the 15 lifecycle states
    metadata_json = Column(Text, nullable=True)             # Additional context / user notes
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="cases")
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="case", cascade="all, delete-orphan")
    authorities = relationship("Authority", back_populates="case", cascade="all, delete-orphan")
    communications = relationship("Communication", back_populates="case", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="case", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="case", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="case", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"

    document_id = Column(String(64), primary_key=True, default=generate_uuid)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    document_type = Column(String(100), nullable=False)  # FREEZE_NOTICE, BANK_STATEMENT, POLICE_NOTICE, etc.
    extracted_text = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=utc_now, nullable=False)
    metadata_json = Column(Text, nullable=True)  # Structured extraction facts, confidence metrics

    case = relationship("Case", back_populates="documents")

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String(100), primary_key=True)  # e.g., TXN-DEMO-001
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    transaction_date = Column(DateTime, default=utc_now, nullable=False)
    dispute_status = Column(String(50), default="DISPUTED", nullable=False)  # DISPUTED, FLAGGED, CLEARED, UNKNOWN
    source = Column(String(100), nullable=False)  # USER_STATEMENT, BANK_ADAPTER, NOTICE_DOC
    description = Column(String(255), nullable=True)

    case = relationship("Case", back_populates="transactions")

class Authority(Base):
    __tablename__ = "authorities"

    authority_id = Column(String(64), primary_key=True, default=generate_uuid)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    authority_name = Column(String(255), nullable=False)
    jurisdiction = Column(String(150), nullable=False)
    reference_number = Column(String(100), nullable=False)  # Notice / FIR / Complaint / Order No
    officer_name = Column(String(150), nullable=True)
    contact_information = Column(String(255), nullable=True)
    source = Column(String(100), nullable=False)  # UPLOADED_NOTICE, BANK_ADAPTER, AUTHORITY_ADAPTER
    confidence = Column(String(20), default="HIGH", nullable=False)  # HIGH, MEDIUM, LOW

    case = relationship("Case", back_populates="authorities")

class Communication(Base):
    __tablename__ = "communications"

    communication_id = Column(String(64), primary_key=True, default=generate_uuid)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    recipient_type = Column(String(100), nullable=False)  # BANK_BRANCH, BANK_NODAL_OFFICER, LAW_ENFORCEMENT, GRIEVANCE
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False)  # DRAFT, EDITED, APPROVED, REJECTED, RECORDED
    created_at = Column(DateTime, default=utc_now, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False)

    case = relationship("Case", back_populates="communications")

class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(String(64), primary_key=True, default=generate_uuid)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    case = relationship("Case", back_populates="tasks")

class Escalation(Base):
    __tablename__ = "escalations"

    escalation_id = Column(String(64), primary_key=True, default=generate_uuid)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    level = Column(String(50), default="LEVEL_1", nullable=False)  # LEVEL_1, LEVEL_2, LEVEL_3
    reason = Column(Text, nullable=False)
    channel = Column(String(150), nullable=False)  # Branch/Case-desk, Nodal/Ombudsman, Legal/Courts
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, IN_PROGRESS, RESOLVED, CLOSED
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    case = relationship("Case", back_populates="escalations")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(String(64), primary_key=True, default=generate_uuid)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=True, index=True)
    actor = Column(String(100), default="SYSTEM", nullable=False)  # USER, SYSTEM, AI_AGENT, COMPLIANCE_OFFICER
    action = Column(String(150), nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
    result = Column(String(50), default="SUCCESS", nullable=False)  # SUCCESS, WARNING, FAILURE, BLOCKED
    details = Column(Text, nullable=True)  # JSON or text description

    case = relationship("Case", back_populates="audit_logs")
