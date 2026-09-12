"""
Multi-Source Reconciliation Module for BankFreeze AI
Compares:
1. User-provided information
2. Uploaded documents
3. Mock bank response
4. Mock authority response
Detects MATCH, MISMATCH, MISSING.
Enforces the safety rule: Critical conflicts block automated resolution recommendations.
"""

from typing import Dict, Any, Optional, List
from schemas.reconciliation import CaseReconciliationResult, FieldComparison, ReconciliationStatus
from schemas.extraction import DocumentExtractionResult, NOT_AVAILABLE_MSG, NOT_PROVIDED_MSG

class MultiSourceReconciler:
    """
    Cross-checks values across user input, document extractions,
    mock bank adapter responses, and mock authority responses.
    """

    def reconcile_case(
        self,
        case_id: str,
        user_info: Dict[str, Any],
        document_result: Optional[DocumentExtractionResult] = None,
        bank_details: Optional[Dict[str, Any]] = None,
        authority_details: Optional[Dict[str, Any]] = None
    ) -> CaseReconciliationResult:
        comparisons: List[FieldComparison] = []
        conflicts: List[str] = []

        # Target fields to reconcile
        target_fields = [
            ("transaction_id", "Transaction ID", True),
            ("amount", "Disputed Amount", True),
            ("reference_number", "Reference / Complaint Number", True),
            ("freeze_reason", "Stated Reason", False),
            ("authority", "Requesting Authority", False)
        ]

        for field_key, field_label, is_critical in target_fields:
            # 1. User value
            user_val = str(user_info.get(field_key) or "").strip()
            if not user_val or user_val.upper() in ["NONE", "N/A", "NULL", ""]:
                user_val = NOT_PROVIDED_MSG

            # 2. Document value
            doc_val = NOT_PROVIDED_MSG
            if document_result:
                fact_attr = getattr(document_result, field_key, None)
                if fact_attr and fact_attr.fact_type.value != "MISSING":
                    doc_val = str(fact_attr.value).strip()

            # 3. Bank value
            bank_val = NOT_PROVIDED_MSG
            if bank_details:
                b_raw = bank_details.get(field_key)
                if field_key == "authority":
                    b_raw = bank_details.get("requesting_authority") or bank_details.get("authority")
                elif field_key == "freeze_reason":
                    b_raw = bank_details.get("reason")
                if b_raw is not None and str(b_raw).strip():
                    bank_val = str(b_raw).strip()

            # 4. Authority value
            auth_val = NOT_PROVIDED_MSG
            if authority_details:
                a_raw = authority_details.get(field_key)
                if field_key == "authority":
                    a_raw = authority_details.get("authority_name") or authority_details.get("authority")
                elif field_key == "amount":
                    a_raw = authority_details.get("disputed_amount")
                elif field_key == "freeze_reason":
                    a_raw = authority_details.get("allegation")
                if a_raw is not None and str(a_raw).strip():
                    auth_val = str(a_raw).strip()

            # Evaluate status across active values
            status, details = self._evaluate_field_status(
                field_key, user_val, doc_val, bank_val, auth_val
            )

            if status == ReconciliationStatus.MISMATCH:
                conflict_msg = f"{field_label} mismatch: {details}"
                conflicts.append(conflict_msg)

            comparisons.append(FieldComparison(
                field_name=field_label,
                user_value=user_val,
                doc_value=doc_val,
                bank_value=bank_val,
                authority_value=auth_val,
                status=status,
                is_critical=is_critical,
                details=details
            ))

        has_critical = any(c.status == ReconciliationStatus.MISMATCH and c.is_critical for c in comparisons)

        overall = "RECONCILED"
        if has_critical:
            overall = "CONFLICT_DETECTED"
        elif any(c.status == ReconciliationStatus.MISSING for c in comparisons if c.is_critical):
            overall = "INFORMATION_MISSING"

        return CaseReconciliationResult(
            case_id=case_id,
            comparisons=comparisons,
            has_critical_conflicts=has_critical,
            conflict_summary=conflicts,
            can_proceed_to_resolution=not has_critical,
            overall_status=overall
        )

    def _normalize_for_comparison(self, key: str, val: str) -> str:
        s = val.lower().strip()
        if key == "amount":
            # Strip currency symbols and commas
            s = s.replace("rs.", "").replace("inr", "").replace("₹", "").replace(",", "").strip()
            try:
                f = float(s)
                return f"{f:.2f}"
            except ValueError:
                pass
        elif key == "transaction_id":
            s = s.replace(" ", "").replace("-", "").replace("/", "")
        elif key == "reference_number":
            s = s.replace(" ", "").replace("-", "").replace("/", "")
        return s

    def _is_empty_or_missing(self, val: str) -> bool:
        return val in [NOT_PROVIDED_MSG, NOT_AVAILABLE_MSG, "", "NONE", "N/A", "UNKNOWN"]

    def _evaluate_field_status(
        self, key: str, user_val: str, doc_val: str, bank_val: str, auth_val: str
    ) -> (ReconciliationStatus, str):
        values = {
            "User": user_val,
            "Document": doc_val,
            "Bank": bank_val,
            "Authority": auth_val
        }

        # Filter active non-missing values
        active = {src: v for src, v in values.items() if not self._is_empty_or_missing(v)}

        if len(active) == 0:
            return ReconciliationStatus.MISSING, "No source provided information for this field."

        if len(active) == 1:
            src = list(active.keys())[0]
            return ReconciliationStatus.PARTIAL, f"Provided only by {src} ({active[src]}); missing in other sources."

        # Compare normalized values
        normalized = {src: self._normalize_for_comparison(key, v) for src, v in active.items()}
        unique_norms = set(normalized.values())

        if len(unique_norms) == 1:
            return ReconciliationStatus.MATCH, f"Consistent across {', '.join(active.keys())}."

        # Soft matching for text fields like freeze_reason or authority
        if key in ["freeze_reason", "authority"]:
            terms = list(unique_norms)
            # Check if any common substring exists
            if any(t1 in t2 or t2 in t1 for i, t1 in enumerate(terms) for t2 in terms[i+1:]):
                return ReconciliationStatus.MATCH, f"Substantially consistent across {', '.join(active.keys())}."

        # Otherwise mismatch
        diff_str = ", ".join([f"{src}: {active[src]}" for src in active.keys()])
        return ReconciliationStatus.MISMATCH, f"Inconsistent values detected across sources ({diff_str})."

reconciler = MultiSourceReconciler()
