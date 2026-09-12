"""
Extraction Schemas with Strict Fact Attribution and Safety Guardrails.
Guarantees value, source, confidence (HIGH/MEDIUM/LOW), and fact_type (EXTRACTED/INFERRED/MISSING).
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from schemas.case import ConfidenceLevel, FactType

NOT_AVAILABLE_MSG = "NOT AVAILABLE IN SUBMITTED INFORMATION"
NOT_PROVIDED_MSG = "NOT PROVIDED"

class Fact(BaseModel):
    value: str = Field(default=NOT_AVAILABLE_MSG)
    source: str = Field(default="NOT PROVIDED")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.LOW)
    fact_type: FactType = Field(default=FactType.MISSING)

    @classmethod
    def missing(cls, field_name: str = "") -> "Fact":
        return cls(
            value=NOT_AVAILABLE_MSG,
            source="NOT PROVIDED",
            confidence=ConfidenceLevel.LOW,
            fact_type=FactType.MISSING
        )

    @classmethod
    def extracted(cls, value: str, source: str, confidence: ConfidenceLevel = ConfidenceLevel.HIGH) -> "Fact":
        if not value or value.strip() == "" or value.strip().upper() in ["NONE", "N/A", "NULL", "UNKNOWN"]:
            return cls.missing()
        return cls(
            value=value.strip(),
            source=source,
            confidence=confidence,
            fact_type=FactType.EXTRACTED
        )

    @classmethod
    def inferred(cls, value: str, source: str, confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM) -> "Fact":
        if not value or value.strip() == "":
            return cls.missing()
        return cls(
            value=value.strip(),
            source=source,
            confidence=confidence,
            fact_type=FactType.INFERRED
        )

class DocumentExtractionResult(BaseModel):
    document_id: Optional[str] = None
    filename: str
    document_type: str = "UNKNOWN"
    
    # Required Extraction Fields
    freeze_reason: Fact = Field(default_factory=lambda: Fact.missing("freeze_reason"))
    restriction_type: Fact = Field(default_factory=lambda: Fact.missing("restriction_type"))
    transaction_id: Fact = Field(default_factory=lambda: Fact.missing("transaction_id"))
    amount: Fact = Field(default_factory=lambda: Fact.missing("amount"))
    transaction_date: Fact = Field(default_factory=lambda: Fact.missing("transaction_date"))
    authority: Fact = Field(default_factory=lambda: Fact.missing("authority"))
    jurisdiction: Fact = Field(default_factory=lambda: Fact.missing("jurisdiction"))
    reference_number: Fact = Field(default_factory=lambda: Fact.missing("reference_number"))
    complaint_number: Fact = Field(default_factory=lambda: Fact.missing("complaint_number"))
    order_number: Fact = Field(default_factory=lambda: Fact.missing("order_number"))
    officer_name: Fact = Field(default_factory=lambda: Fact.missing("officer_name"))
    contact_information: Fact = Field(default_factory=lambda: Fact.missing("contact_information"))

    # Summary of missing facts
    missing_fields: List[str] = Field(default_factory=list)
    raw_text: Optional[str] = None

    def compute_missing_fields(self):
        """Identify which required fields could not be extracted."""
        fields = [
            ("freeze_reason", self.freeze_reason),
            ("restriction_type", self.restriction_type),
            ("transaction_id", self.transaction_id),
            ("amount", self.amount),
            ("transaction_date", self.transaction_date),
            ("authority", self.authority),
            ("jurisdiction", self.jurisdiction),
            ("reference_number", self.reference_number),
            ("complaint_number", self.complaint_number),
            ("order_number", self.order_number),
            ("officer_name", self.officer_name),
            ("contact_information", self.contact_information),
        ]
        self.missing_fields = [name for name, fact in fields if fact.fact_type == FactType.MISSING]
