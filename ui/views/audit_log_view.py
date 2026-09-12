"""
Audit Log View for BankFreeze AI
Displays immutable chronological audit records for compliance, governance, and traceability.
"""

from typing import Optional
import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.models import AuditLog, Case
from ui.components import render_status_badge

def render_audit_log_view(db: Session, case_id: Optional[str] = None):
    st.markdown("## 📜 Immutable System & Case Audit Trail")
    st.caption("Cryptographically traceable chronological record of every system action, user approval, and agent dispatch.")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        view_scope = st.selectbox("Audit Scope", ["Current Case Only" if case_id else "All Cases", "All Cases"])
    with col2:
        actor_filter = st.selectbox("Filter by Actor", ["All Actors", "USER", "AI_AGENT", "SYSTEM"])
    with col3:
        result_filter = st.selectbox("Filter by Result", ["All Results", "SUCCESS", "WARNING", "FAILURE", "BLOCKED"])

    query = db.query(AuditLog)
    if view_scope == "Current Case Only" and case_id:
        query = query.filter(AuditLog.case_id == case_id)
    if actor_filter != "All Actors":
        query = query.filter(AuditLog.actor == actor_filter)
    if result_filter != "All Results":
        query = query.filter(AuditLog.result == result_filter)

    logs = query.order_by(AuditLog.timestamp.desc()).all()

    if not logs:
        st.info("No audit logs match the current query parameters.")
        return

    table_data = []
    for l in logs:
        table_data.append({
            "Log ID": l.log_id[:8] + "...",
            "Case ID": l.case_id or "GLOBAL",
            "Actor": l.actor,
            "Action": l.action,
            "Result": l.result,
            "Timestamp (UTC)": l.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        })

    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### 🔍 Inspect Log Entry Metadata")
    log_map = {f"{l.timestamp.strftime('%H:%M:%S')} - {l.action} ({l.actor})": l for l in logs}
    selected_log_label = st.selectbox("Select entry to view complete JSON payload:", list(log_map.keys()))
    if selected_log_label:
        entry = log_map[selected_log_label]
        st.json({
            "log_id": entry.log_id,
            "case_id": entry.case_id,
            "actor": entry.actor,
            "action": entry.action,
            "result": entry.result,
            "timestamp": entry.timestamp.isoformat(),
            "details": entry.details
        })
