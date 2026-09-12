"""
Case Details View for BankFreeze AI
Provides full case dossier: header, status badges, 15-state lifecycle stepper,
transaction particulars, authority references, missing facts, and audit timeline.
"""

import streamlit as st
import json
from sqlalchemy.orm import Session

from database.models import Case, Document, Transaction, Authority, AuditLog, Task
from ui.components import render_status_badge, render_confidence_badge, render_metric_card
from schemas.case import CaseStatus
from modules.audit import log_audit

LIFECYCLE_ORDER = [
    "NEW", "BANK_VERIFICATION", "AUTHORITY_IDENTIFICATION",
    "AUTHORITY_INQUIRY_REQUIRED", "WAITING_FOR_INFORMATION", "INFORMATION_RECEIVED",
    "CASE_ANALYSIS", "ACTION_REQUIRED", "USER_REVIEW", "APPROVED",
    "COMMUNICATION_RECORDED", "FOLLOW_UP_REQUIRED", "ESCALATION_REQUIRED",
    "RESOLVED", "CLOSED"
]

def render_case_details(db: Session, case_id: str):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        st.error(f"Case {case_id} not found.")
        return

    # Header section
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"## 📁 Case Dossier: `{case.case_id}`")
        st.caption(f"Registered on {case.created_at.strftime('%d %b %Y, %H:%M UTC')} | Last updated {case.updated_at.strftime('%d %b %Y, %H:%M UTC')}")
    with col_h2:
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        st.markdown(f"**Current Status:** {render_status_badge(case.status)}", unsafe_allow_html=True)

    # Lifecycle Stepper
    with st.expander("📍 **Case Lifecycle Progression (15 States)**", expanded=False):
        current_idx = LIFECYCLE_ORDER.index(case.status) if case.status in LIFECYCLE_ORDER else 0
        stepper_cols = st.columns(len(LIFECYCLE_ORDER))
        for idx, state_name in enumerate(LIFECYCLE_ORDER):
            with stepper_cols[idx]:
                if idx < current_idx:
                    icon = "✅"
                elif idx == current_idx:
                    icon = "🔵"
                else:
                    icon = "⚪"
                # Short label
                short_name = state_name.replace("_", " ")
                st.caption(f"{icon}\n**{short_name}**")

        st.divider()
        c_adv1, c_adv2 = st.columns([3, 1])
        with c_adv1:
            new_state = st.selectbox("Manually Transition Lifecycle Stage:", LIFECYCLE_ORDER, index=current_idx)
        with c_adv2:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Advance Stage ➔"):
                if new_state != case.status:
                    old_s = case.status
                    case.status = new_state
                    log_audit(db, action="MANUAL_LIFECYCLE_TRANSITION", actor="USER", case_id=case_id, details={"from": old_s, "to": new_state})
                    db.commit()
                    st.success(f"Case transitioned to {new_state}!")
                    st.rerun()

    # Core Facts Cards
    txns = db.query(Transaction).filter(Transaction.case_id == case_id).all()
    auth = db.query(Authority).filter(Authority.case_id == case_id).first()
    docs = db.query(Document).filter(Document.case_id == case_id).all()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Bank Name", case.bank_name, "🏦")
    with c2:
        render_metric_card("Account Number", case.masked_account_number, "🔒")
    with c3:
        render_metric_card("Restriction Type", case.restriction_type, "🚫")
    with c4:
        amt_str = f"₹{txns[0].amount:,.2f}" if txns else "NOT PROVIDED"
        render_metric_card("Disputed Amount", amt_str, "💰")

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    # Detailed dossier tabs
    tab_overview, tab_evidence, tab_timeline = st.tabs(["📌 Case Overview & Particulars", "🔍 Evidence & Source Attribution", "⏳ Event & Audit Timeline"])

    with tab_overview:
        col_o1, col_o2 = st.columns(2)
        with col_o1:
            st.markdown("##### 📝 Case Particulars")
            st.markdown(f"- **Stated Freeze Reason:** {case.freeze_reason}")
            st.markdown(f"- **Date Restriction Observed:** {case.freeze_date.strftime('%Y-%m-%d')}")
            if txns:
                st.markdown(f"- **Disputed Transaction ID:** `{txns[0].transaction_id}`")
                st.markdown(f"- **Transaction Date:** {txns[0].transaction_date.strftime('%Y-%m-%d')}")
                st.markdown(f"- **Dispute Status:** `{txns[0].dispute_status}`")
            else:
                st.markdown("- **Disputed Transaction:** *NOT PROVIDED*")

            # Parse user narrative if stored
            if case.metadata_json:
                try:
                    meta = json.loads(case.metadata_json)
                    if meta.get("narrative"):
                        st.info(f"**Account Holder Statement:** {meta['narrative']}")
                except Exception:
                    pass

        with col_o2:
            st.markdown("##### 🏛️ Authority & Legal Reference")
            if auth:
                st.markdown(f"- **Requesting Authority:** **{auth.authority_name}**")
                st.markdown(f"- **Jurisdiction:** {auth.jurisdiction}")
                st.markdown(f"- **Statutory / Notice Ref No:** `{auth.reference_number}`")
                st.markdown(f"- **Officer Name:** {auth.officer_name or 'NOT PROVIDED'}")
                st.markdown(f"- **Contact Info:** {auth.contact_information or 'NOT PROVIDED'}")
                st.markdown(f"- **Information Source:** `{auth.source}`")
                st.markdown(f"- **Source Confidence:** {render_confidence_badge(auth.confidence)}", unsafe_allow_html=True)
            else:
                st.warning("⚠️ No authority identified yet. Run **Documents** analysis or **Multi-Source Reconciliation** to detect authority.")

    with tab_evidence:
        st.markdown("##### 📄 Attached Documentary Evidence")
        if not docs:
            st.info("No documents uploaded yet. Go to the **Documents** view to upload the bank intimation or police notice.")
        else:
            for d in docs:
                with st.expander(f"📁 {d.filename} ({d.document_type}) - Uploaded {d.uploaded_at.strftime('%Y-%m-%d %H:%M')}"):
                    st.text_area("Extracted Document Content", d.extracted_text or "[No text extracted]", height=180, disabled=True, key=f"dossier_doc_{d.document_id}")

    with tab_timeline:
        st.markdown("##### 📜 Chronological Audit & Activity Timeline")
        logs = db.query(AuditLog).filter(AuditLog.case_id == case_id).order_by(AuditLog.timestamp.desc()).all()
        if not logs:
            st.caption("No log entries recorded for this case.")
        else:
            for log in logs:
                st.markdown(f"""
                <div class="timeline-item">
                    <div class="timeline-time">{log.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')} | Actor: <strong>{log.actor}</strong></div>
                    <div class="timeline-title">{log.action} ({log.result})</div>
                    <div class="timeline-desc">{log.details or 'No additional metadata'}</div>
                </div>
                """, unsafe_allow_html=True)
