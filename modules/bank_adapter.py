"""
Bank Adapter Module for BankFreeze AI
Defines the BankAdapterBase interface and a MockBankAdapter providing synthetic test data.
All data is clearly labeled as [DEMO DATA].
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
from config.settings import settings

class BankAdapterBase(ABC):
    """
    Abstract Base Class for Bank Integration.
    A future AuthorizedBankAdapter will implement this interface to connect to actual core banking systems.
    """

    @abstractmethod
    def get_account_status(self, account_identifier: str) -> Dict[str, Any]:
        """Fetch current operational and freeze status of an account."""
        pass

    @abstractmethod
    def get_freeze_details(self, account_identifier: str) -> Dict[str, Any]:
        """Fetch official freeze metadata, restricting authority, reference number, and lien amount."""
        pass

    @abstractmethod
    def get_transaction_details(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Fetch details of a disputed or flagged transaction."""
        pass

class MockBankAdapter(BankAdapterBase):
    """
    Mock Bank Adapter returning synthetic records.
    Explicitly labeled as DEMO DATA.
    """

    def __init__(self, latency: Optional[float] = None):
        self.latency = latency if latency is not None else settings.MOCK_BANK_LATENCY
        
        # Synthetic database of demo accounts
        self._demo_records = {
            "CASE-DEMO-001": {
                "account_number": "XXXX-XXXX-1001",
                "bank_name": "State Bank of India",
                "status": "RESTRICTED",
                "restriction_type": "DEBIT_FREEZE",
                "reason": "LAW_ENFORCEMENT_REQUEST",
                "transaction_id": "TXN-DEMO-001",
                "amount": 18500.0,
                "reference_number": "LEA-DEMO-001",
                "requesting_authority": "Cyber Crime Unit",
                "jurisdiction": "Hyderabad",
                "officer_name": "Insp. K. Sharma (Cyber Cell)",
                "contact_info": "cybercrime-hyd-demo@police.gov.in",
                "data_badge": "[DEMO DATA]"
            },
            "CASE-DEMO-002": {
                "account_number": "XXXX-XXXX-2002",
                "bank_name": "HDFC Bank",
                "status": "RESTRICTED",
                "restriction_type": "LIEN_AMOUNT",
                "reason": "CYBERCRIME_COMPLAINT_1930",
                "transaction_id": "TXN-DEMO-002",
                "amount": 54200.0,
                "reference_number": "NCRRP-2025-88412",
                "requesting_authority": "National Cyber Crime Reporting Portal (NCRRP)",
                "jurisdiction": "New Delhi / NCR",
                "officer_name": "Nodal Desk Cyber Division",
                "contact_info": "nodal-cyber-demo@gov.in",
                "data_badge": "[DEMO DATA]"
            },
            "CASE-DEMO-003": {
                "account_number": "XXXX-XXXX-3003",
                "bank_name": "ICICI Bank",
                "status": "RESTRICTED",
                "restriction_type": "TOTAL_FREEZE",
                "reason": "KYC_NON_COMPLIANCE",
                "transaction_id": "TXN-DEMO-003",
                "amount": 0.0,
                "reference_number": "BNK-KYC-99012",
                "requesting_authority": "Bank Internal Risk & Compliance",
                "jurisdiction": "Mumbai Central",
                "officer_name": "Branch Operations Manager",
                "contact_info": "kyc-compliance-demo@icici-mock.com",
                "data_badge": "[DEMO DATA]"
            },
            "CASE-DEMO-004": {
                "account_number": "XXXX-XXXX-4004",
                "bank_name": "Axis Bank",
                "status": "RESTRICTED",
                "restriction_type": "TOTAL_FREEZE",
                "reason": "COURT_ATTACHMENT_ORDER",
                "transaction_id": "TXN-DEMO-004",
                "amount": 250000.0,
                "reference_number": "SEC91-COURT-2025-04",
                "requesting_authority": "Hon'ble Chief Metropolitan Magistrate Court",
                "jurisdiction": "Bengaluru",
                "officer_name": "Registrar / Judicial Bench-3",
                "contact_info": "cmm-bengaluru-demo@ecourts.gov.in",
                "data_badge": "[DEMO DATA]"
            },
            "CASE-DEMO-005": {
                "account_number": "XXXX-XXXX-5005",
                "bank_name": "Punjab National Bank",
                "status": "RESTRICTED",
                "restriction_type": "DEBIT_FREEZE",
                "reason": "INTERNAL_AML_ALERT",
                "transaction_id": "TXN-DEMO-005",
                "amount": 78000.0,
                "reference_number": "AML-ALERT-771",
                "requesting_authority": "AML Suspicious Activity Unit",
                "jurisdiction": "Kolkata",
                "officer_name": "Senior AML Investigator",
                "contact_info": "aml-desk-demo@pnb-mock.in",
                "data_badge": "[DEMO DATA]"
            }
        }

    def _simulate_delay(self):
        if self.latency > 0:
            time.sleep(self.latency)

    def get_account_status(self, account_identifier: str) -> Dict[str, Any]:
        self._simulate_delay()
        
        # Search by case_id or account number
        for case_id, data in self._demo_records.items():
            if case_id == account_identifier or data["account_number"] == account_identifier:
                return {
                    "is_restricted": True,
                    "status": data["status"],
                    "restriction_type": data["restriction_type"],
                    "bank_name": data["bank_name"],
                    "account_number": data["account_number"],
                    "notice": "Account restricted as per regulatory/statutory notice.",
                    "data_classification": "[DEMO DATA - SYNTHETIC MOCK]"
                }
        
        # Default synthetic response for newly created cases
        return {
            "is_restricted": True,
            "status": "RESTRICTED",
            "restriction_type": "DEBIT_FREEZE",
            "bank_name": "Mock Partner Bank",
            "account_number": account_identifier,
            "notice": "Account hold initiated following compliance flag.",
            "data_classification": "[DEMO DATA - SYNTHETIC MOCK]"
        }

    def get_freeze_details(self, account_identifier: str) -> Dict[str, Any]:
        self._simulate_delay()
        
        for case_id, data in self._demo_records.items():
            if case_id == account_identifier or data["account_number"] == account_identifier:
                return {
                    "status": data["status"],
                    "restriction_type": data["restriction_type"],
                    "reason": data["reason"],
                    "transaction_id": data["transaction_id"],
                    "amount": data["amount"],
                    "reference_number": data["reference_number"],
                    "requesting_authority": data["requesting_authority"],
                    "jurisdiction": data["jurisdiction"],
                    "officer_name": data["officer_name"],
                    "contact_information": data["contact_info"],
                    "data_classification": "[DEMO DATA - SYNTHETIC MOCK]"
                }
        
        # Fallback synthetic record
        return {
            "status": "RESTRICTED",
            "restriction_type": "DEBIT_FREEZE",
            "reason": "LAW_ENFORCEMENT_REQUEST",
            "transaction_id": "TXN-DEMO-001",
            "amount": 18500.0,
            "reference_number": "LEA-DEMO-001",
            "requesting_authority": "Cyber Crime Unit",
            "jurisdiction": "Hyderabad",
            "officer_name": "Insp. K. Sharma (Cyber Cell)",
            "contact_information": "cybercrime-hyd-demo@police.gov.in",
            "data_classification": "[DEMO DATA - SYNTHETIC MOCK]"
        }

    def get_transaction_details(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        self._simulate_delay()
        
        for case_id, data in self._demo_records.items():
            if data["transaction_id"] == transaction_id:
                return {
                    "transaction_id": data["transaction_id"],
                    "amount": data["amount"],
                    "dispute_status": "FLAGGED",
                    "source": "MOCK_BANK_CORE",
                    "description": f"Transfer marked under notice {data['reference_number']}",
                    "data_classification": "[DEMO DATA - SYNTHETIC MOCK]"
                }
        
        return {
            "transaction_id": transaction_id,
            "amount": 18500.0,
            "dispute_status": "FLAGGED",
            "source": "MOCK_BANK_CORE",
            "description": "Disputed transaction flagged in interbank nodal settlement",
            "data_classification": "[DEMO DATA - SYNTHETIC MOCK]"
        }
