"""
Multi-Source Reconciliation View for BankFreeze AI
Compares records across User Intake, Uploaded Documents, Mock Bank Adapter, and Mock Authority Adapter.
Identifies MATCH, MISMATCH, MISSING, and flags critical conflicts that block automated resolution.
"""

import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.models import Case, Document, Transaction, Authority
from modules.bank_adapter import MockBankAdapter
from modules.authority_adapter import MockAuthorityAdapter
from modules.document_analyzer import document_analyzer
from modules.reconciliation import reconciler
from modules.audit import log_audit
from ui.components import render_reconciliation_badge

def render_reconciliation_view(db: Session, case_id: str):
    st.markdown("## ⚖️ Multi-Source Cross-Verification & Reconciliation")
    st.caption("Compares facts across 4 independent vectors: User Intake, Uploaded Documents, Bank Core, and Authority Registry.")

    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        st.error("Case not found.")
        return

    # Collect source 1: User intake
    txns = db.query(Transaction).filter(Transaction.case_id == case_id).all()
    user_info = {
        "transaction_id": txns[0].transaction_id if txns else "NOT PROVIDED",
        "amount": str(txns[0].amount) if txns else "NOT PROVIDED",
        "freeze_reason": case.freeze_reason,
        "authority": "NOT PROVIDED",
        "reference_number": "NOT PROVIDED"
    }

    # Collect source 2: Uploaded Documents
    docs = db.query(Document).filter(Document.case_id == case_id).all()
    doc_res = None
    if docs:
        doc_res = document_analyzer.analyze_document(docs[0].extracted_text or "", docs[0].filename)

    # Collect source 3: Mock Bank Adapter
    bank_adapter = MockBankAdapter()
    bank_info = bank_adapter.get_freeze_details(case.case_id)

    # Collect source 4: Mock Authority Adapter
    auth_adapter = MockAuthorityAdapter()
    auth_rec = db.query(Authority).filter(Authority.case_id == case_id).first()
    ref_no = auth_rec.reference_number if auth_rec else bank_info.get("reference_number", "LEA-DEMO-001")
    auth_info = auth_adapter.get_case_information(ref_no)

    # Execute Reconciliation
    res = reconciler.reconcile_case(
        case_id=case_id,
        user_info=user_info,
        document_result=doc_res,
        bank_details=bank_info,
        authority_details=auth_info
    )

    # Log reconciliation run
    log_audit(
        db,
        action="RUN_SOURCE_RECONCILIATION",
        actor="SYSTEM",
        case_id=case_id,
        result="SUCCESS",
        details={"has_critical_conflicts": res.has_critical_conflicts, "overall": res.overall_status}
    )

    # Conflict Warning Banner if conflicts detected
    if res.has_critical_conflicts:
        st.error(
            "🚨 **CRITICAL CONFLICT DETECTED:** One or more key parameters (Amount, Transaction ID, or Reference Number) "
            "conflict between submitted notices and adapter records. Automated final resolution is strictly **BLOCKED** "
            "to prevent misrepresentation. Factual clarification must be sought from the Bank Nodal Desk first."
        )
        with st.expander("⚠️ View Detailed Conflict Breakdown", expanded=True):
            for c in res.conflict_summary:
                st.markdown(f"- 🔴 **{c}**")
    else:
        st.success("✅ **Cross-Verification Successful:** Core factual parameters are consistent across available sources.")

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    # Render Side-by-Side Comparison Matrix Table
    rows_html = []
    for comp in res.comparisons:
        status_badge = render_reconciliation_badge(comp.status.value)
        crit_tag = "<span style='color: #dc2626; font-weight: 700; font-size: 0.75rem;'>[CRITICAL]</span>" if comp.is_critical else ""
        rows_html.append(f"""
        <tr>
            <td style="padding: 10px 12px; font-weight: 600;">{comp.field_name} {crit_tag}</td>
            <td style="padding: 10px 12px; font-family: monospace; font-size: 0.85rem;">{comp.user_value}</td>
            <td style="padding: 10px 12px; font-family: monospace; font-size: 0.85rem;">{comp.doc_value}</td>
            <td style="padding: 10px 12px; font-family: monospace; font-size: 0.85rem;">{comp.bank_value}</td>
            <td style="padding: 10px 12px; font-family: monospace; font-size: 0.85rem;">{comp.authority_value}</td>
            <td style="padding: 10px 12px; text-align: center;">{status_badge}</td>
        </tr>
        <tr>
            <td colspan="6" style="padding: 4px 12px 10px 12px; font-size: 0.8rem; color: #64748b; border-bottom: 1px solid #e2e8f0; background-color: #fafafa;">
                <em>Notes: {comp.details}</em>
            </td>
        </tr>
        """)

    matrix_html = f"""
    <table style="width: 100%; border-collapse: collapse; font-size: 0.88rem;">
        <thead>
            <tr style="background-color: #0f172a; color: #ffffff; text-align: left;">
                <th style="padding: 10px 12px;">Parameter</th>
                <th style="padding: 10px 12px;">1. User Intake</th>
                <th style="padding: 10px 12px;">2. Document</th>
                <th style="padding: 10px 12px;">3. Bank Adapter</th>
                <th style="padding: 10px 12px;">4. Authority Adapter</th>
                <th style="padding: 10px 12px; text-align: center;">Verification</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows_html)}
        </tbody>
    </table>
    """
    st.markdown(matrix_html, unsafe_allow_html=True)
