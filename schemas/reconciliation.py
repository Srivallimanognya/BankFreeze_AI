"""
Reconciliation Schemas for Cross-Source Verification.
Compares: User, Document, Bank Adapter, Authority Adapter.
Detects: MATCH, MISMATCH, MISSING.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ReconciliationStatus(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    MISSING = "MISSING"
    PARTIAL = "PARTIAL"

class FieldComparison(BaseModel):
    field_name: str
    user_value: str = Field(default="NOT PROVIDED")
    doc_value: str = Field(default="NOT PROVIDED")
    bank_value: str = Field(default="NOT PROVIDED")
    authority_value: str = Field(default="NOT PROVIDED")
    status: ReconciliationStatus = ReconciliationStatus.MISSING
    is_critical: bool = False
    details: str = ""

class CaseReconciliationResult(BaseModel):
    case_id: str
    comparisons: List[FieldComparison] = Field(default_factory=list)
    has_critical_conflicts: bool = False
    conflict_summary: List[str] = Field(default_factory=list)
    can_proceed_to_resolution: bool = True
    overall_status: str = "PENDING"
