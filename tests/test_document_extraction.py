"""
Unit tests for Document Analyzer & Structured Fact Extraction.
Validates extraction accuracy and anti-hallucination guardrails.
"""

import pytest
from modules.document_analyzer import document_analyzer
from schemas.case import FactType, ConfidenceLevel

SAMPLE_NOTICE_TEXT = """
CYBER CRIME POLICE STATION, HYDERABAD
Requisition Notice under Section 91 Cr.P.C. / IT Act
Ref No: LEA-DEMO-001
Date: 12-08-2025

To,
The Nodal Officer, State Bank of India
Hyderabad Branch

Subject: Debit Freeze in Complaint No: CC-HYD-2025-0811

Sir/Madam,
An amount of Rs. 18500.00 has been transferred into Bank Account ending in 1001 under Transaction ID: TXN-DEMO-001 on 10-08-2025.
You are hereby directed to immediately effect DEBIT FREEZE on the said account.

Investigating Officer: Inspector K. Sharma
Contact Email: cybercrime-hyd-demo@police.gov.in
Jurisdiction: Hyderabad, Telangana
"""

def test_extraction_of_available_facts():
    res = document_analyzer.analyze_document(SAMPLE_NOTICE_TEXT, "demo_notice.txt")
    
    assert res.transaction_id.fact_type == FactType.EXTRACTED
    assert res.transaction_id.value == "TXN-DEMO-001"
    
    assert res.amount.fact_type == FactType.EXTRACTED
    assert float(res.amount.value) == 18500.0
    
    assert res.reference_number.fact_type == FactType.EXTRACTED
    assert res.reference_number.value == "LEA-DEMO-001"
    
    assert res.complaint_number.fact_type == FactType.EXTRACTED
    assert res.complaint_number.value == "CC-HYD-2025-0811"
    
    assert res.officer_name.fact_type == FactType.EXTRACTED
    assert "Inspector K. Sharma" in res.officer_name.value
    
    assert res.restriction_type.fact_type == FactType.EXTRACTED
    assert res.restriction_type.value == "DEBIT_FREEZE"

def test_anti_hallucination_on_missing_facts():
    # Provide a document with missing order number and missing contact info
    text_with_missing_fields = """
    ICICI BANK NOTICE
    Your account is placed on hold due to KYC update overdue.
    Notice Ref: BNK-001
    """
    res = document_analyzer.analyze_document(text_with_missing_fields, "short_notice.txt")
    
    # Missing fields must NEVER be hallucinated
    assert res.order_number.fact_type == FactType.MISSING
    assert res.order_number.value == "NOT AVAILABLE IN SUBMITTED INFORMATION"
    
    assert res.transaction_id.fact_type == FactType.MISSING
    assert res.transaction_id.value == "NOT AVAILABLE IN SUBMITTED INFORMATION"
    
    assert res.officer_name.fact_type == FactType.MISSING
    assert res.officer_name.value == "NOT AVAILABLE IN SUBMITTED INFORMATION"
    
    # Check that missing fields list includes them
    assert "order_number" in res.missing_fields
    assert "transaction_id" in res.missing_fields
    assert "officer_name" in res.missing_fields
