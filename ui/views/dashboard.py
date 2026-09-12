"""
Dashboard View for BankFreeze AI
Displays high-level KPIs, case lifecycle distribution, quick actions, and filterable case ledger.
"""

import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database.models import Case, Transaction, Authority, Document
from ui.components import render_metric_card, render_status_badge

def render_dashboard(db: Session):
    st.markdown("## 📊 Investigation Operations Dashboard")
    st.caption("Real-time monitoring and case dispatch overview across active account freeze investigations.")

    cases = db.query(Case).all()
    total_cases = len(cases)

    # Compute key status counts
    new_cases = sum(1 for c in cases if c.status == "NEW")
    under_inv = sum(1 for c in cases if c.status in ["CASE_ANALYSIS", "BANK_VERIFICATION", "AUTHORITY_IDENTIFICATION", "AUTHORITY_INQUIRY_REQUIRED", "INFORMATION_RECEIVED"])
    waiting_resp = sum(1 for c in cases if c.status == "WAITING_FOR_INFORMATION")
    followup_req = sum(1 for c in cases if c.status == "FOLLOW_UP_REQUIRED")
    escalation_req = sum(1 for c in cases if c.status == "ESCALATION_REQUIRED")
    resolved_cases = sum(1 for c in cases if c.status in ["RESOLVED", "CLOSED"])

    # Render Metric Cards in responsive columns
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Total Cases", total_cases, "📁")
    with c2:
        render_metric_card("New Intake", new_cases, "🆕")
    with c3:
        render_metric_card("Under Investigation", under_inv, "🔍")
    with c4:
        render_metric_card("Waiting Response", waiting_resp, "⏳")

    st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        render_metric_card("Follow-Up Required", followup_req, "🔔")
    with c6:
        render_metric_card("Escalation Required", escalation_req, "🚨")
    with c7:
        render_metric_card("Resolved / Closed", resolved_cases, "✅")
    with c8:
        action_req = sum(1 for c in cases if c.status in ["ACTION_REQUIRED", "USER_REVIEW", "APPROVED"])
        render_metric_card("Action Required", action_req, "⚡")

    st.divider()

    # Case Ledger Table & Filters
    st.markdown("### 📋 Active Investigation Cases")
    
    col_filter1, col_filter2, col_search = st.columns([1, 1, 2])
    with col_filter1:
        bank_filter = st.selectbox("Filter by Bank", ["All Banks"] + sorted(list({c.bank_name for c in cases})))
    with col_filter2:
        status_filter = st.selectbox("Filter by Status", ["All Statuses"] + sorted(list({c.status for c in cases})))
    with col_search:
        search_query = st.text_input("Search Case ID, Stated Reason, or Account", "")

    # Filter records
    filtered = cases
    if bank_filter != "All Banks":
        filtered = [c for c in filtered if c.bank_name == bank_filter]
    if status_filter != "All Statuses":
        filtered = [c for c in filtered if c.status == status_filter]
    if search_query:
        sq = search_query.lower()
        filtered = [c for c in filtered if sq in c.case_id.lower() or sq in c.freeze_reason.lower() or sq in c.masked_account_number.lower()]

    if not filtered:
        st.info("No cases match the selected filter criteria.")
    else:
        table_data = []
        for c in filtered:
            table_data.append({
                "Case ID": c.case_id,
                "Bank": c.bank_name,
                "Account": c.masked_account_number,
                "Restriction Type": c.restriction_type,
                "Status": c.status,
                "Stated Reason": c.freeze_reason[:55] + ("..." if len(c.freeze_reason) > 55 else ""),
                "Freeze Date": c.freeze_date.strftime("%Y-%m-%d"),
            })

        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Quick Case Jump
    st.markdown("#### 🚀 Quick Case Jump")
    case_ids = [c.case_id for c in cases]
    if case_ids:
        c_sel, c_btn = st.columns([3, 1])
        with c_sel:
            selected_case = st.selectbox("Select a case to inspect immediately:", case_ids, key="dash_quick_jump")
        with c_btn:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Open Case Dossier ➔", use_container_width=True):
                st.session_state["selected_case_id"] = selected_case
                st.session_state["active_page"] = "Case Details"
                st.rerun()
