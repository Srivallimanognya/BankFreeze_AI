"""
Freeze Classification Module for BankFreeze AI
Classifies bank freeze events into standard legal/banking categories:
DISPUTED_TRANSACTION, CYBERCRIME_COMPLAINT, POLICE_REQUEST, COURT_ORDER,
KYC_RELATED, AML_RELATED, SUSPICIOUS_TRANSACTION, BANK_INTERNAL_REVIEW, UNKNOWN.
"""

from typing import Dict, Any, Optional
from schemas.case import FreezeCategory, ConfidenceLevel
from schemas.extraction import DocumentExtractionResult

class FreezeClassificationResult:
    def __init__(self, category: FreezeCategory, confidence: ConfidenceLevel, evidence: str, source: str):
        self.category = category
        self.confidence = confidence
        self.evidence = evidence
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "confidence": self.confidence.value,
            "evidence": self.evidence,
            "source": self.source
        }

class FreezeAnalyzer:
    """
    Evaluates documentary facts, stated reasons, and adapter details
    to classify the legal basis of the restriction.
    """

    def classify(
        self,
        stated_reason: Optional[str] = None,
        document_result: Optional[DocumentExtractionResult] = None,
        bank_freeze_details: Optional[Dict[str, Any]] = None
    ) -> FreezeClassificationResult:
        combined_text_parts = []
        sources = []

        if stated_reason and stated_reason != "NOT PROVIDED":
            combined_text_parts.append(f"User Stated Reason: {stated_reason}")
            sources.append("User Intake")

        if document_result and document_result.raw_text:
            combined_text_parts.append(f"Document Text: {document_result.raw_text}")
            sources.append(f"Document ({document_result.filename})")

        if bank_freeze_details:
            bank_reason = bank_freeze_details.get("reason", "")
            req_auth = bank_freeze_details.get("requesting_authority", "")
            combined_text_parts.append(f"Bank Record: reason={bank_reason}, authority={req_auth}")
            sources.append("Bank Adapter")

        combined = " ".join(combined_text_parts).lower()
        source_str = " + ".join(sources) if sources else "System Heuristics"

        # Classification rules ordered by specificity
        
        # 1. Court Order / Judicial attachment
        if any(w in combined for w in ["court order", "magistrate", "section 102", "section 91", "judicial", "injunction", "attachment order"]):
            evidence = "Document or record references formal court order / statutory section under CrPC."
            return FreezeClassificationResult(FreezeCategory.COURT_ORDER, ConfidenceLevel.HIGH, evidence, source_str)

        # 2. Cybercrime Complaint (NCRRP / 1930 / MHA portal)
        if any(w in combined for w in ["1930", "ncrrp", "cyber crime", "cybercrime", "national cyber crime", "mha portal", "phishing complaint"]):
            evidence = "Identified law enforcement Cyber Crime / NCRRP 1930 incident acknowledgment."
            return FreezeClassificationResult(FreezeCategory.CYBERCRIME_COMPLAINT, ConfidenceLevel.HIGH, evidence, source_str)

        # 3. Police Request / Law Enforcement without specific cyber notice
        if any(w in combined for w in ["police request", "police station", "sub-inspector", "investigating officer", "crime branch"]):
            evidence = "Formal inquiry/hold request received directly from police station."
            return FreezeClassificationResult(FreezeCategory.POLICE_REQUEST, ConfidenceLevel.HIGH, evidence, source_str)

        # 4. KYC Related
        if any(w in combined for w in ["re-kyc", "c-kyc", "kyc non-compliance", "periodic kyc", "pan card update", "identity document missing"]):
            evidence = "Account restriction attributed to overdue periodic customer identification / Re-KYC."
            return FreezeClassificationResult(FreezeCategory.KYC_RELATED, ConfidenceLevel.HIGH, evidence, source_str)

        # 5. AML Related / FIU
        if any(w in combined for w in ["aml", "anti-money laundering", "str alert", "financial intelligence", "velocity check", "suspicious activity unit"]):
            evidence = "Transaction pattern triggered internal Anti-Money Laundering / STR thresholds."
            return FreezeClassificationResult(FreezeCategory.AML_RELATED, ConfidenceLevel.HIGH, evidence, source_str)

        # 6. Disputed Transaction / P2P / Chargeback
        if any(w in combined for w in ["dispute", "chargeback", "p2p", "merchant dispute", "reversal request"]):
            evidence = "Restriction stems from specific disputed counterparty fund transfer."
            return FreezeClassificationResult(FreezeCategory.DISPUTED_TRANSACTION, ConfidenceLevel.MEDIUM, evidence, source_str)

        # 7. Suspicious Transaction
        if any(w in combined for w in ["suspicious transaction", "fraud alert", "unauthorized transfer"]):
            evidence = "Flagged under bank automated fraud detection heuristics."
            return FreezeClassificationResult(FreezeCategory.SUSPICIOUS_TRANSACTION, ConfidenceLevel.MEDIUM, evidence, source_str)

        # 8. Bank Internal Review
        if any(w in combined for w in ["internal review", "branch operations", "dormant", "lien marked by branch"]):
            evidence = "Operational hold initiated internally by branch management."
            return FreezeClassificationResult(FreezeCategory.BANK_INTERNAL_REVIEW, ConfidenceLevel.LOW, evidence, source_str)

        # 9. Unknown
        return FreezeClassificationResult(
            FreezeCategory.UNKNOWN,
            ConfidenceLevel.LOW,
            "Insufficient documentary or operational evidence to determine precise category.",
            source_str
        )

freeze_analyzer = FreezeAnalyzer()
