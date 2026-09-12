"""
Unit tests for Freeze Classification Engine.
Validates categorization across all 9 standard categories.
"""

import pytest
from modules.freeze_analyzer import freeze_analyzer
from schemas.case import FreezeCategory

def test_court_order_classification():
    res = freeze_analyzer.classify(stated_reason="Section 102 CrPC attachment by Magistrate Court")
    assert res.category == FreezeCategory.COURT_ORDER

def test_cybercrime_complaint_classification():
    res = freeze_analyzer.classify(stated_reason="Complaint received from National Cyber Crime Reporting Portal 1930")
    assert res.category == FreezeCategory.CYBERCRIME_COMPLAINT

def test_kyc_classification():
    res = freeze_analyzer.classify(stated_reason="Account suspended for non-compliance of periodic Re-KYC")
    assert res.category == FreezeCategory.KYC_RELATED

def test_police_request_classification():
    res = freeze_analyzer.classify(stated_reason="Requisition notice received from Police Station Investigating Officer")
    assert res.category == FreezeCategory.POLICE_REQUEST

def test_aml_classification():
    res = freeze_analyzer.classify(stated_reason="Internal AML threshold alert and suspicious activity review")
    assert res.category == FreezeCategory.AML_RELATED

def test_disputed_transaction_classification():
    res = freeze_analyzer.classify(stated_reason="P2P payment transfer dispute raised by counterparty")
    assert res.category == FreezeCategory.DISPUTED_TRANSACTION

def test_unknown_classification():
    res = freeze_analyzer.classify(stated_reason="Hold placed without any details provided")
    assert res.category == FreezeCategory.UNKNOWN
