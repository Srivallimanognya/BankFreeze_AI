"""
Pydantic Models and Enums for Cases and Lifecycle Management.
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class CaseStatus(str, Enum):
    NEW = "NEW"
    BANK_VERIFICATION = "BANK_VERIFICATION"
    AUTHORITY_IDENTIFICATION = "AUTHORITY_IDENTIFICATION"
    AUTHORITY_INQUIRY_REQUIRED = "AUTHORITY_INQUIRY_REQUIRED"
    WAITING_FOR_INFORMATION = "WAITING_FOR_INFORMATION"
    INFORMATION_RECEIVED = "INFORMATION_RECEIVED"
    CASE_ANALYSIS = "CASE_ANALYSIS"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    USER_REVIEW = "USER_REVIEW"
    APPROVED = "APPROVED"
    COMMUNICATION_RECORDED = "COMMUNICATION_RECORDED"
    FOLLOW_UP_REQUIRED = "FOLLOW_UP_REQUIRED"
    ESCALATION_REQUIRED = "ESCALATION_REQUIRED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class RestrictionType(str, Enum):
    TOTAL_FREEZE = "TOTAL_FREEZE"
    DEBIT_FREEZE = "DEBIT_FREEZE"
    CREDIT_FREEZE = "CREDIT_FREEZE"
    LIEN_AMOUNT = "LIEN_AMOUNT"
    ACCOUNT_SUSPENSION = "ACCOUNT_SUSPENSION"
    UNKNOWN = "UNKNOWN"

class FreezeCategory(str, Enum):
    DISPUTED_TRANSACTION = "DISPUTED_TRANSACTION"
    CYBERCRIME_COMPLAINT = "CYBERCRIME_COMPLAINT"
    POLICE_REQUEST = "POLICE_REQUEST"
    COURT_ORDER = "COURT_ORDER"
    KYC_RELATED = "KYC_RELATED"
    AML_RELATED = "AML_RELATED"
    SUSPICIOUS_TRANSACTION = "SUSPICIOUS_TRANSACTION"
    BANK_INTERNAL_REVIEW = "BANK_INTERNAL_REVIEW"
    UNKNOWN = "UNKNOWN"

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class FactType(str, Enum):
    EXTRACTED = "EXTRACTED"
    INFERRED = "INFERRED"
    MISSING = "MISSING"

class CaseCreate(BaseModel):
    bank_name: str = Field(..., min_length=2, max_length=150)
    account_number: str = Field(..., min_length=4, max_length=50)
    freeze_date: Optional[datetime] = None
    restriction_type: RestrictionType = RestrictionType.UNKNOWN
    freeze_reason: str = Field(default="NOT PROVIDED")
    user_narrative: Optional[str] = None
    disputed_amount: Optional[float] = None
    transaction_id: Optional[str] = None

class CaseResponse(BaseModel):
    case_id: str
    user_id: str
    bank_name: str
    masked_account_number: str
    freeze_date: datetime
    restriction_type: str
    freeze_reason: str
    status: CaseStatus
    created_at: datetime
    updated_at: datetime
    metadata_json: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
