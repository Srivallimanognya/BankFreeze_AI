"""
Document Analyzer Module for BankFreeze AI
Accepts PDF, PNG, JPG, TXT documents. Extracts raw text and parses structured facts
with strict attribution, confidence ratings, and anti-hallucination guardrails.
"""

import io
import re
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from PIL import Image

from schemas.extraction import DocumentExtractionResult, Fact, NOT_AVAILABLE_MSG, NOT_PROVIDED_MSG
from schemas.case import ConfidenceLevel, FactType
from modules.llm_service import llm_service
from modules.security import sanitize_and_redact_text

logger = logging.getLogger(__name__)

class DocumentAnalyzer:
    """
    Extracts text from files and parses financial & statutory legal freeze facts.
    """

    def extract_text_from_file(self, file_bytes: bytes, filename: str) -> str:
        """Extract text based on file extension (PDF, TXT, PNG, JPG)."""
        ext = Path(filename).suffix.lower()
        text = ""

        if ext == ".txt":
            try:
                text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text = file_bytes.decode("latin-1", errors="ignore")

        elif ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                pages = [page.extract_text() or "" for page in reader.pages]
                text = "\n".join(pages)
            except Exception as e:
                logger.warning(f"Error reading PDF {filename} with pypdf: {e}")
                # Simple ASCII scan fallback if PDF library encounters a stream error
                text = re.sub(r"[^\x20-\x7E\n]", " ", file_bytes.decode("ascii", errors="ignore"))

        elif ext in [".png", ".jpg", ".jpeg"]:
            # Try pytesseract if available, otherwise return descriptive synthetic image tag
            try:
                import pytesseract
                image = Image.open(io.BytesIO(file_bytes))
                text = pytesseract.image_to_string(image)
            except Exception:
                text = f"[IMAGE DOCUMENT: {filename} - Text extraction requires OCR engine. Notice scanned.]"

        else:
            try:
                text = file_bytes.decode("utf-8", errors="ignore")
            except Exception:
                text = f"[Binary or unhandled format: {filename}]"

        return sanitize_and_redact_text(text.strip())

    def analyze_document(self, raw_text: str, filename: str) -> DocumentExtractionResult:
        """
        Analyze extracted document text and return a strict DocumentExtractionResult.
        Guarantees that missing fields are marked NOT AVAILABLE IN SUBMITTED INFORMATION.
        """
        result = DocumentExtractionResult(
            filename=filename,
            document_type=self._classify_document_type(raw_text, filename),
            raw_text=raw_text
        )

        if not raw_text or len(raw_text.strip()) < 5:
            result.compute_missing_fields()
            return result

        # Step 1: Run deterministic heuristic extractor
        extracted = self._heuristic_extraction(raw_text, filename)
        
        # Step 2: If LLM is configured, enrich with LLM without inventing facts
        if llm_service.is_configured():
            llm_facts = self._llm_extraction(raw_text, filename)
            # Merge with strict validation: only accept non-empty values
            for field, fact in llm_facts.items():
                if hasattr(extracted, field):
                    existing = getattr(extracted, field)
                    if existing.fact_type == FactType.MISSING and fact.fact_type != FactType.MISSING:
                        setattr(extracted, field, fact)

        extracted.compute_missing_fields()
        return extracted

    def _classify_document_type(self, text: str, filename: str) -> str:
        lower = (text + " " + filename).lower()
        if any(w in lower for w in ["cyber crime", "ncrrp", "1930", "fir", "police station", "investigating officer"]):
            return "POLICE_OR_CYBER_NOTICE"
        if any(w in lower for w in ["section 91", "section 102", "crpc", "magistrate", "court order", "sub-divisional"]):
            return "COURT_ORDER"
        if any(w in lower for w in ["kyc", "re-kyc", "c-kyc", "periodic update", "identity proof"]):
            return "KYC_NOTICE"
        if any(w in lower for w in ["statement of account", "transaction summary", "ledger", "debit / credit"]):
            return "BANK_STATEMENT"
        if any(w in lower for w in ["freeze", "lien", "restriction notice", "hold notice"]):
            return "BANK_FREEZE_NOTICE"
        return "GENERAL_DOCUMENT"

    def _heuristic_extraction(self, text: str, filename: str) -> DocumentExtractionResult:
        """Extract structured fields using robust regex and context parsers."""
        res = DocumentExtractionResult(
            filename=filename,
            document_type=self._classify_document_type(text, filename),
            raw_text=text
        )
        source_label = f"Document: {filename}"

        # 1. Transaction ID
        txn_match = re.search(r"\b(TXN-[A-Z0-9-]+|UPI/\d+|UTR[A-Z0-9]+|REF/\d+)\b", text, re.I)
        if txn_match:
            res.transaction_id = Fact.extracted(txn_match.group(1), source_label, ConfidenceLevel.HIGH)

        # 2. Amount
        amt_match = re.search(r"(?:Rs\.?|INR|₹|\bAmount\s*[:=]?\s*)\s*([\d,]+(?:\.\d{2})?)", text, re.I)
        if amt_match:
            clean_amt = amt_match.group(1).replace(",", "")
            try:
                val = float(clean_amt)
                res.amount = Fact.extracted(f"{val:.2f}", source_label, ConfidenceLevel.HIGH)
            except ValueError:
                pass

        # 3. Reference Number
        ref_match = re.search(r"(?:Reference\s*(?:No|Number)?|Ref\s*No\.?|Order\s*No\.?)\s*[:=-]?\s*([A-Z0-9\-_/]+)", text, re.I)
        if ref_match and ref_match.group(1).strip() not in ["N/A", "NONE"]:
            res.reference_number = Fact.extracted(ref_match.group(1).strip(), source_label, ConfidenceLevel.HIGH)

        # 4. Complaint Number
        comp_match = re.search(r"(?:Complaint\s*(?:No|Number)?|Ack\s*(?:No|Number)?|Ack\s*ID)\s*[:=-]?\s*([A-Z0-9\-_/]+)", text, re.I)
        if comp_match:
            res.complaint_number = Fact.extracted(comp_match.group(1).strip(), source_label, ConfidenceLevel.HIGH)

        # 5. Order Number
        ord_match = re.search(r"(?:Court\s*Order\s*(?:No|Number)?|Order\s*(?:No|Number)?)\s*[:=-]?\s*([A-Z0-9\-_/]+)", text, re.I)
        if ord_match:
            res.order_number = Fact.extracted(ord_match.group(1).strip(), source_label, ConfidenceLevel.HIGH)

        # 6. Transaction Date
        date_match = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b", text)
        if date_match:
            res.transaction_date = Fact.extracted(date_match.group(1), source_label, ConfidenceLevel.MEDIUM)

        # 7. Authority Name
        auth_patterns = [
            r"(Cyber\s+Crime\s+(?:Police\s+Station|Cell|Unit|Division))",
            r"(National\s+Cyber\s+Crime\s+Reporting\s+Portal(?:\s*\([A-Z]+\))?)",
            r"((?:Hon'?ble\s+)?(?:Chief\s+Metropolitan\s+Magistrate|District|High)\s+Court)",
            r"(Bank\s+Internal\s+Risk(?:\s*&\s*Compliance)?)",
            r"(State\s+Police\s+Cyber\s+Cell)",
            r"(Financial\s+Intelligence\s+Unit(?:\s*-\s*India)?)"
        ]
        for pat in auth_patterns:
            m = re.search(pat, text, re.I)
            if m:
                res.authority = Fact.extracted(m.group(1).strip(), source_label, ConfidenceLevel.HIGH)
                break

        # 8. Officer Name
        off_match = re.search(r"(?:Inspector|Insp\.|Sub-Inspector|SI|Officer|Registrar|IO)\s+([A-Z][a-zA-Z\.\s]+?)(?:,|\n|\(|;|$)", text)
        if off_match:
            candidate = off_match.group(0).strip().rstrip(",;")
            if len(candidate) < 50:
                res.officer_name = Fact.extracted(candidate, source_label, ConfidenceLevel.HIGH)

        # 9. Contact Information
        contact_matches = []
        emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
        phones = re.findall(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}\b", text)
        if emails:
            contact_matches.extend(emails)
        if phones:
            contact_matches.extend(phones)
        if "1930" in text:
            contact_matches.append("Helpline: 1930")
        if contact_matches:
            res.contact_information = Fact.extracted(" / ".join(list(dict.fromkeys(contact_matches))), source_label, ConfidenceLevel.HIGH)

        # 10. Jurisdiction
        juris_match = re.search(r"(?:Jurisdiction|Location|District|City|Station)\s*[:=-]?\s*([A-Za-z\s,/-]+?)(?:\.|\n|;|$)", text, re.I)
        if juris_match:
            j_str = juris_match.group(1).strip()
            if 3 < len(j_str) < 60:
                res.jurisdiction = Fact.extracted(j_str, source_label, ConfidenceLevel.MEDIUM)

        # 11. Freeze Reason
        if "cybercrime" in text.lower() or "1930" in text.lower():
            res.freeze_reason = Fact.extracted("Cybercrime Complaint via NCRRP / Law Enforcement", source_label, ConfidenceLevel.HIGH)
        elif "section 102" in text.lower() or "section 91" in text.lower():
            res.freeze_reason = Fact.extracted("Statutory Notice under Section 91 / 102 CrPC", source_label, ConfidenceLevel.HIGH)
        elif "kyc" in text.lower():
            res.freeze_reason = Fact.extracted("Periodic Re-KYC Non-Compliance", source_label, ConfidenceLevel.HIGH)
        elif "dispute" in text.lower() or "p2p" in text.lower():
            res.freeze_reason = Fact.extracted("Disputed Transaction / Chargeback Notice", source_label, ConfidenceLevel.HIGH)
        elif "aml" in text.lower():
            res.freeze_reason = Fact.extracted("Anti-Money Laundering Internal Hold", source_label, ConfidenceLevel.HIGH)

        # 12. Restriction Type
        if "lien" in text.lower():
            res.restriction_type = Fact.extracted("LIEN_AMOUNT", source_label, ConfidenceLevel.HIGH)
        elif "debit freeze" in text.lower() or "debit hold" in text.lower():
            res.restriction_type = Fact.extracted("DEBIT_FREEZE", source_label, ConfidenceLevel.HIGH)
        elif "total freeze" in text.lower() or "total hold" in text.lower() or "complete freeze" in text.lower():
            res.restriction_type = Fact.extracted("TOTAL_FREEZE", source_label, ConfidenceLevel.HIGH)

        return res

    def _llm_extraction(self, text: str, filename: str) -> Dict[str, Fact]:
        """Prompt LLM to extract facts while forbidding hallucination."""
        system_prompt = (
            "You are a forensic legal-banking document extractor. "
            "Extract ONLY facts explicitly present in the document. "
            "CRITICAL SAFETY RULE: NEVER invent or hallucinate police officers, FIRs, complaint numbers, "
            "amounts, or transaction IDs. If a field is not present in the text, return 'NOT PROVIDED'."
        )
        prompt = f"""
Document Filename: {filename}
Document Text:
---
{text[:4000]}
---

Extract the following in strictly valid JSON format:
{{
  "freeze_reason": "explicit reason or NOT PROVIDED",
  "restriction_type": "DEBIT_FREEZE | TOTAL_FREEZE | LIEN_AMOUNT | UNKNOWN or NOT PROVIDED",
  "transaction_id": "value or NOT PROVIDED",
  "amount": "value or NOT PROVIDED",
  "transaction_date": "value or NOT PROVIDED",
  "authority": "value or NOT PROVIDED",
  "jurisdiction": "value or NOT PROVIDED",
  "reference_number": "value or NOT PROVIDED",
  "complaint_number": "value or NOT PROVIDED",
  "order_number": "value or NOT PROVIDED",
  "officer_name": "value or NOT PROVIDED",
  "contact_information": "value or NOT PROVIDED"
}}
"""
        response_text = llm_service.complete(prompt, system_prompt=system_prompt, json_mode=True)
        facts = {}
        if response_text:
            try:
                data = json.loads(response_text)
                for k, v in data.items():
                    if v and str(v).strip().upper() not in ["NOT PROVIDED", "NOT AVAILABLE IN SUBMITTED INFORMATION", "NONE", "N/A"]:
                        facts[k] = Fact.extracted(str(v).strip(), f"LLM Extracted from {filename}", ConfidenceLevel.HIGH)
            except Exception as e:
                logger.warning(f"Error parsing LLM response JSON: {e}")
        return facts

document_analyzer = DocumentAnalyzer()
