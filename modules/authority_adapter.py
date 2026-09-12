"""
Authority Adapter Module for BankFreeze AI
Defines the AuthorityAdapterBase interface and a MockAuthorityAdapter providing synthetic law-enforcement responses.
All data is clearly labeled as [DEMO DATA].
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
import uuid
from config.settings import settings

class AuthorityAdapterBase(ABC):
    """
    Abstract Base Class for Law Enforcement / Statutory Authority Integrations.
    Future AuthorizedAuthorityIntegration will implement this interface.
    """

    @abstractmethod
    def get_authority_details(self, authority_identifier: str) -> Dict[str, Any]:
        """Fetch official jurisdiction, station/court details, and contact directory."""
        pass

    @abstractmethod
    def get_case_information(self, reference_number: str) -> Dict[str, Any]:
        """Query case metadata corresponding to a reference/complaint/notice number."""
        pass

    @abstractmethod
    def submit_inquiry(self, case_id: str, inquiry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a formal inquiry or clarification representation."""
        pass

    @abstractmethod
    def get_response_status(self, inquiry_id: str) -> Dict[str, Any]:
        """Poll the processing status of a submitted inquiry."""
        pass

class MockAuthorityAdapter(AuthorityAdapterBase):
    """
    Mock Authority Adapter returning synthetic demo records.
    Strictly isolated prototype with NO connection to real police or legal databases.
    """

    def __init__(self, latency: Optional[float] = None):
        self.latency = latency if latency is not None else settings.MOCK_AUTHORITY_LATENCY
        
        # Inquiries state store (synthetic)
        self._submitted_inquiries = {}
        
        # Synthetic authority database
        self._demo_authorities = {
            "LEA-DEMO-001": {
                "authority_name": "Cyber Crime Police Station",
                "jurisdiction": "Cyberabad / Hyderabad, Telangana",
                "reference_number": "LEA-DEMO-001",
                "complaint_number": "CC-HYD-2025-0811",
                "officer_name": "Inspector K. Sharma",
                "contact_info": "cyberps-hyd-demo@police.gov.in / 040-2345XXXX",
                "status": "UNDER_INVESTIGATION",
                "allegation": "Unauthorized P2P transfer dispute reported by victim",
                "disputed_amount": 18500.0,
                "transaction_id": "TXN-DEMO-001",
                "required_documents": [
                    "Identity proof (Aadhaar/PAN)",
                    "Bank statement showing origin of disputed funds",
                    "Explanation / proof of commercial transaction / P2P order receipt"
                ],
                "data_badge": "[DEMO DATA]"
            },
            "NCRRP-2025-88412": {
                "authority_name": "National Cyber Crime Reporting Portal (NCRRP / 1930)",
                "jurisdiction": "Central Cyber Cell, New Delhi",
                "reference_number": "NCRRP-2025-88412",
                "complaint_number": "1930-ACK-88412-2025",
                "officer_name": "Nodal Desk Cyber Division",
                "contact_info": "cyberportal-demo@mha.gov.in / Helpline 1930",
                "status": "LIEN_REQUESTED",
                "allegation": "Layered fund trace from reported phishing fraud",
                "disputed_amount": 54200.0,
                "transaction_id": "TXN-DEMO-002",
                "required_documents": [
                    "Full KYC documents",
                    "6-month bank statement",
                    "Written representation addressed to IO with transaction justification"
                ],
                "data_badge": "[DEMO DATA]"
            },
            "BNK-KYC-99012": {
                "authority_name": "Bank Internal Risk & Compliance",
                "jurisdiction": "Mumbai Central",
                "reference_number": "BNK-KYC-99012",
                "complaint_number": "INTERNAL-KYC-99012",
                "officer_name": "Branch Operations Manager",
                "contact_info": "kyc-compliance-demo@icici-mock.com",
                "status": "DOCUMENTS_AWAITED",
                "allegation": "Failure to complete periodic Re-KYC within statutory timeline",
                "disputed_amount": 0.0,
                "transaction_id": "TXN-DEMO-003",
                "required_documents": [
                    "Recent passport size photograph",
                    "Original Officially Valid Document (OVD) for in-person verification",
                    "Latest address proof"
                ],
                "data_badge": "[DEMO DATA]"
            },
            "SEC91-COURT-2025-04": {
                "authority_name": "Hon'ble Chief Metropolitan Magistrate Court",
                "jurisdiction": "Bengaluru Rural District",
                "reference_number": "SEC91-COURT-2025-04",
                "complaint_number": "CC-NO-4402/2025",
                "officer_name": "Registrar / Judicial Bench-3",
                "contact_info": "cmm-bengaluru-demo@ecourts.gov.in",
                "status": "JUDICIAL_ATTACHMENT",
                "allegation": "Order passed under Section 102 CrPC / Sec 91 CrPC in pending civil/criminal dispute",
                "disputed_amount": 250000.0,
                "transaction_id": "TXN-DEMO-004",
                "required_documents": [
                    "Vakalatnama by legal counsel",
                    "Formal application for account de-freezing / bond under Sec 451/457 CrPC"
                ],
                "data_badge": "[DEMO DATA]"
            },
            "AML-ALERT-771": {
                "authority_name": "Financial Intelligence & AML Review Desk",
                "jurisdiction": "Kolkata Regional Directorate",
                "reference_number": "AML-ALERT-771",
                "complaint_number": "STR-ALERT-771-KOL",
                "officer_name": "Senior AML Investigator",
                "contact_info": "aml-desk-demo@pnb-mock.in",
                "status": "ENHANCED_DUE_DILIGENCE",
                "allegation": "High velocity debit/credit pattern inconsistent with declared customer profile",
                "disputed_amount": 78000.0,
                "transaction_id": "TXN-DEMO-005",
                "required_documents": [
                    "Source of income / Income tax returns (past 2 years)",
                    "Invoices or agreements backing high-value credits"
                ],
                "data_badge": "[DEMO DATA]"
            }
        }

    def _simulate_delay(self):
        if self.latency > 0:
            time.sleep(self.latency)

    def get_authority_details(self, authority_identifier: str) -> Dict[str, Any]:
        self._simulate_delay()
        for ref, data in self._demo_authorities.items():
            if ref == authority_identifier or data["authority_name"] == authority_identifier:
                return {
                    "authority_name": data["authority_name"],
                    "jurisdiction": data["jurisdiction"],
                    "contact_info": data["contact_info"],
                    "officer_name": data["officer_name"],
                    "data_classification": "[DEMO DATA - SYNTHETIC MOCK]"
                }
        return {
            "authority_name": "Cyber Crime Investigation Unit",
            "jurisdiction": "State Police Cyber Cell",
            "contact_info": "investigation-demo@police.gov.in",
            "officer_name": "Investigating Officer (IO)",
            "data_classification": "[DEMO DATA - SYNTHETIC MOCK]"
        }

    def get_case_information(self, reference_number: str) -> Dict[str, Any]:
        self._simulate_delay()
        if reference_number in self._demo_authorities:
            rec = self._demo_authorities[reference_number]
            return {
                "found": True,
                "reference_number": rec["reference_number"],
                "complaint_number": rec["complaint_number"],
                "authority_name": rec["authority_name"],
                "jurisdiction": rec["jurisdiction"],
                "officer_name": rec["officer_name"],
                "contact_info": rec["contact_info"],
                "status": rec["status"],
                "allegation": rec["allegation"],
                "disputed_amount": rec["disputed_amount"],
                "transaction_id": rec["transaction_id"],
                "required_documents": rec["required_documents"],
                "data_classification": "[DEMO DATA - SYNTHETIC MOCK]"
            }
        
        # If reference number is not recognized
        return {
            "found": False,
            "reference_number": reference_number,
            "status": "NOT_FOUND_IN_DEMO_RECORDS",
            "note": "Reference number not located in synthetic mock authority registry.",
            "data_classification": "[DEMO DATA - SYNTHETIC MOCK]"
        }

    def submit_inquiry(self, case_id: str, inquiry_data: Dict[str, Any]) -> Dict[str, Any]:
        self._simulate_delay()
        ack_id = f"INQ-MOCK-{uuid.uuid4().hex[:8].upper()}"
        self._submitted_inquiries[ack_id] = {
            "case_id": case_id,
            "inquiry_data": inquiry_data,
            "status": "SUBMITTED_FOR_REVIEW",
            "submitted_at": time.time(),
            "expected_response_window": "3-5 business days"
        }
        return {
            "acknowledgment_id": ack_id,
            "status": "ACKNOWLEDGED",
            "message": "Mock inquiry logged successfully. (Note: Synthetic demo mode - no actual dispatch).",
            "expected_response_window": "3-5 business days",
            "data_classification": "[DEMO DATA - SYNTHETIC MOCK]"
        }

    def get_response_status(self, inquiry_id: str) -> Dict[str, Any]:
        self._simulate_delay()
        if inquiry_id in self._submitted_inquiries:
            rec = self._submitted_inquiries[inquiry_id]
            return {
                "inquiry_id": inquiry_id,
                "status": rec["status"],
                "expected_response_window": rec["expected_response_window"],
                "data_classification": "[DEMO DATA - SYNTHETIC MOCK]"
            }
        return {
            "inquiry_id": inquiry_id,
            "status": "NOT_FOUND",
            "data_classification": "[DEMO DATA - SYNTHETIC MOCK]"
        }
