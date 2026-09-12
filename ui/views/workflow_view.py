"""
ui/views/workflow_view.py
-------------------------
BANKFREEZE AI - n8n Workflow Integration View

DEMO / PROTOTYPE MODULE
-----------------------
Allows the user to trigger the n8n agentic workflow for a selected case
and inspect the complete, structured investigation result inline.

Flow:
Streamlit UI (Case Selection)
    ↓
Trigger n8n Workflow
    ↓
n8n Agentic Workflow / Investigation Engine
    ↓
AI Case Analysis & Risk Assessment
    ↓
Procedural Recommendation & Human Review
    ↓
Return Structured JSON Response
    ↓
Streamlit Complete Investigation Dashboard (Inline)
"""

import json
from typing import Any, Dict
import streamlit as st
from sqlalchemy.orm import Session

from config.settings import settings
from database.models import Case
from modules.workflow_client import trigger_n8n_workflow, build_webhook_payload
from ui.components import render_status_badge


def render_workflow_view(db: Session, active_case_id: str | None) -> None:
    st.markdown("## 🔗 n8n Workflow Investigation & Resolution")
    st.caption(
        "DEMO / PROTOTYPE  |  Trigger the n8n agentic workflow for the active case "
        "and inspect the full investigation result directly in BankFreeze AI."
    )

    # ---- Architecture Guardrail Banner ----
    st.info(
        "**ARCHITECTURE GUARDRAIL ACTIVE**\n\n"
        "This platform operates in demonstration/prototype mode using mock data only. "
        "No real core banking APIs or confidential law-enforcement networks are connected. "
        "No passwords, PINs, OTPs, or credentials are requested or stored.",
        icon="🛡️",
    )

    # ---- Webhook Status ----
    webhook_url: str = (settings.N8N_WEBHOOK_URL or "").strip()
    if webhook_url:
        st.success(
            f"**n8n Webhook Configured:** `{webhook_url[:65]}{'...' if len(webhook_url) > 65 else ''}`",
            icon="✅",
        )
    else:
        st.warning(
            "**n8n Webhook URL Not Configured (Offline Demo Mode Active)**\n\n"
            "The dashboard is fully operational using the built-in local agentic synthesizer. "
            "To connect live n8n cloud, set `N8N_WEBHOOK_URL` in `.env`.",
            icon="⚙️",
        )

    st.markdown("---")

    # ---- Case Selector (Synchronized with Global State) ----
    st.markdown("### 1. Select Case to Trigger")

    all_cases = db.query(Case).order_by(Case.case_id.asc()).all()
    if not all_cases:
        st.warning("No cases found in database. Please initialize seed cases.")
        return

    case_lookup = {c.case_id: c for c in all_cases}
    case_ids = [c.case_id for c in all_cases]

    # Pre-select matching the global active case
    curr_active_id = st.session_state.get("selected_case_id")
    default_idx = case_ids.index(curr_active_id) if curr_active_id in case_ids else 0

    def _on_case_select():
        chosen = st.session_state.get("workflow_page_case_selector")
        if chosen:
            st.session_state["selected_case_id"] = chosen

    selected_case_id = st.selectbox(
        "Select Investigation Case:",
        case_ids,
        index=default_idx,
        format_func=lambda cid: f"{cid} — {case_lookup[cid].bank_name} [{case_lookup[cid].restriction_type}]",
        key="workflow_page_case_selector",
        on_change=_on_case_select,
    )

    # Lock session state to selected case
    st.session_state["selected_case_id"] = selected_case_id
    selected_case = case_lookup[selected_case_id]

    # ---- Payload Preview ----
    with st.expander(f"🔍 Preview Webhook Payload for {selected_case_id}", expanded=False):
        payload_preview = build_webhook_payload(selected_case)
        st.json(payload_preview)
        st.caption(
            "🔒 Guaranteed: Account numbers are masked. Full credentials, PINs, and OTPs "
            "are strictly omitted. The exact payload displayed above is transmitted to n8n."
        )

    st.markdown("---")

    # ---- Trigger Workflow Button ----
    col_btn, col_info = st.columns([2, 5])
    with col_btn:
        trigger_clicked = st.button(
            "🚀 Trigger n8n Workflow",
            type="primary",
            use_container_width=True,
        )
    with col_info:
        if webhook_url:
            st.caption(
                f"📡 Live Mode: Transmitting case `{selected_case_id}` to n8n webhook "
                f"(Timeout: {settings.N8N_TIMEOUT_SECONDS}s)."
            )
        else:
            st.caption(
                f"💻 Offline Mode: Executing local agentic investigation synthesizer for `{selected_case_id}`."
            )

    # Handle workflow execution
    if trigger_clicked:
        with st.spinner(f"Triggering investigation workflow for {selected_case_id}..."):
            workflow_result = trigger_n8n_workflow(selected_case)
            st.session_state[f"workflow_result_{selected_case_id}"] = workflow_result
            st.session_state["last_executed_case_id"] = selected_case_id

    # Retrieve last execution result for the current case
    active_result = st.session_state.get(f"workflow_result_{selected_case_id}")

    # ---- Display Structured Investigation Result ----
    if active_result:
        st.markdown("---")
        _render_investigation_dashboard(selected_case_id, active_result)


def _render_investigation_dashboard(selected_case_id: str, result_dict: Dict[str, Any]) -> None:
    """
    Renders the executive BankFreeze AI investigation result dashboard.
    """
    st.markdown("## 🛡️ BANKFREEZE AI — INVESTIGATION RESULT")

    source = result_dict.get("source", "unknown")
    status_code = result_dict.get("status_code", 200)
    is_demo = result_dict.get("demo_mode", False)
    err_msg = result_dict.get("error")

    # Banner declaring the source
    if source == "n8n_live":
        st.success(
            f"✅ **Investigation Completed via Live n8n Workflow** | HTTP {status_code}",
            icon="🌐",
        )
    elif source == "n8n_live_synthesized":
        st.info(
            f"ℹ️ **n8n Webhook Acknowledged (HTTP {status_code})** — Full Investigation Result Synthesized by Agentic Engine.",
            icon="⚡",
        )
    else:
        st.info(
            "ℹ️ **Investigation Completed via BankFreeze AI Agentic Synthesizer** (Safe Demonstration Mode)",
            icon="🛡️",
        )

    if err_msg and source != "n8n_live":
        st.caption(f"Notice: {err_msg}")

    # Extract user_result object
    resp = result_dict.get("response", {})
    user_res = resp.get("user_result") if isinstance(resp, dict) else None

    # Fallback normalization if n8n returned non-nested structure
    if not user_res and isinstance(resp, dict):
        user_res = resp

    if not isinstance(user_res, dict):
        st.error("No structured investigation result returned.")
        if resp:
            with st.expander("Raw Output"):
                st.json(resp)
        return

    # Extract sections
    case_info = user_res.get("case_information") or {}
    ai_assessment = user_res.get("ai_assessment") or {}
    risk_assessment = user_res.get("risk_assessment") or {}
    findings = user_res.get("investigation_findings") or []
    missing_info = user_res.get("missing_information") or []
    recommended_action = user_res.get("recommended_action") or "NOT PROVIDED"
    human_review = user_res.get("human_review") or {}
    communication = user_res.get("communication") or {}
    account_action = user_res.get("account_action") or {}
    final_status = user_res.get("final_status") or resp.get("final_status") or "COMPLETED"

    # 1. CASE INFORMATION
    st.markdown("### 📋 Case Information")
    c_col1, c_col2, c_col3 = st.columns(3)
    with c_col1:
        st.markdown(f"**Case ID:** `{case_info.get('case_id', selected_case_id)}`")
        st.markdown(f"**Bank:** {case_info.get('bank_name', 'NOT PROVIDED')}")
    with c_col2:
        st.markdown(f"**Masked Account:** `{case_info.get('masked_account_number', 'XXXX-XXXX-XXXX')}`")
        st.markdown(f"**Restriction Type:** `{case_info.get('restriction_type', 'NOT PROVIDED')}`")
    with c_col3:
        st.markdown(f"**Status:** {case_info.get('status', 'NOT PROVIDED')}")
        st.markdown(f"**Freeze Reason:** {case_info.get('freeze_reason', 'NOT PROVIDED')}")

    st.markdown("---")

    # 2. AI ASSESSMENT & RISK ASSESSMENT
    st.markdown("### 🤖 AI Assessment & Multi-Source Reconciliation")
    r_col1, r_col2 = st.columns([1, 2])
    with r_col1:
        r_level = risk_assessment.get("risk_level", "NORMAL")
        if "MISMATCH" in r_level or "HIGH" in r_level:
            st.error(f"**Risk Level:** {r_level}")
        elif "HOLD" in r_level or "LIEN" in r_level:
            st.warning(f"**Risk Level:** {r_level}")
        else:
            st.success(f"**Risk Level:** {r_level}")
        st.caption(f"**Risk Rationale:** {risk_assessment.get('reason', 'NOT PROVIDED')}")

    with r_col2:
        st.markdown(f"**Next Procedural Step:** {ai_assessment.get('next_action', 'NOT PROVIDED')}")

    # Expandable details on Knowns / Unknowns / Conflicts
    with st.expander("AI Fact Breakdown (Knowns, Unknowns, Conflicts)", expanded=True):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            st.markdown("##### 📌 Known Information")
            knowns = ai_assessment.get("known_information") or []
            if knowns:
                for k in knowns:
                    st.markdown(f"- {k}")
            else:
                st.caption("No known points listed.")

            st.markdown("##### ⚖️ Matching Facts")
            matches = ai_assessment.get("matches") or []
            if matches:
                for m in matches:
                    st.markdown(f"- {m}")
            else:
                st.caption("No matching points recorded.")

        with f_col2:
            st.markdown("##### ❓ Unknown Information")
            unknowns = ai_assessment.get("unknown_information") or []
            if unknowns:
                for u in unknowns:
                    st.markdown(f"- {u}")
            else:
                st.caption("No unknown items identified.")

            st.markdown("##### ⚠️ Information Conflicts")
            conflicts = ai_assessment.get("conflicts") or []
            if conflicts:
                for c in conflicts:
                    st.markdown(f"- {c}")
            else:
                st.caption("No conflicting values found.")

    st.markdown("---")

    # 3. INVESTIGATION FINDINGS
    st.markdown("### 🔍 Investigation Findings")
    if findings:
        for item in findings:
            st.markdown(f"- {item}")
    else:
        st.caption("No specific investigation findings recorded.")

    st.markdown("---")

    # 4. MISSING INFORMATION
    st.markdown("### ⚠️ Missing Information & Required Clarifications")
    if missing_info:
        for m in missing_info:
            st.markdown(f"- {m}")
    else:
        st.caption("No critical missing information detected.")

    st.markdown("---")

    # 5. RECOMMENDED ACTION
    st.markdown("### 💡 Recommended Procedural Action")
    st.info(f"**Recommendation:** `{recommended_action}`", icon="📋")

    st.markdown("---")

    # 6. HUMAN REVIEW
    st.markdown("### 👤 Human Review & Authorization")
    hr_col1, hr_col2, hr_col3 = st.columns(3)
    with hr_col1:
        st.markdown(f"**Review Required:** {'Yes' if human_review.get('required', True) else 'No'}")
    with hr_col2:
        st.markdown(f"**Decision:** `{human_review.get('decision', 'APPROVED')}`")
    with hr_col3:
        st.markdown(f"**Approval Channel:** `{human_review.get('approval_channel', 'demo_input')}`")

    st.markdown("---")

    # 7. COMMUNICATION DRAFT
    st.markdown("### ✉️ Generated Communication Draft")
    st.markdown(f"**Status:** `{communication.get('status', 'DEMO_RECORDED')}`")
    if communication.get("subject"):
        st.markdown(f"**Subject:** *{communication.get('subject')}*")
    st.text_area(
        "Communication Message (Factual Inquiry Only):",
        value=communication.get("body", "NOT PROVIDED"),
        height=180,
        disabled=True,
    )

    st.markdown("---")

    # 8. ACCOUNT ACTION & SAFETY DECLARATION
    st.markdown("### 🛑 Account Action & Safety Protocol")
    action_taken = account_action.get("action_taken", "NO AUTOMATIC UNFREEZE")
    note = account_action.get("note", "No automatic account unfreeze is performed by this prototype.")
    st.warning(
        f"**ACTION TAKEN:** {action_taken}\n\n"
        f"**Safety Protocol:** {note}\n\n"
        "BankFreeze AI never claims an account will be unfrozen automatically and does not invoke bank unfreeze triggers.",
        icon="🔒",
    )

    # 9. FINAL STATUS
    st.markdown(f"**Workflow Final Status:** `{final_status}`")

    # 10. RAW JSON EXPANDER (FOR DEBUGGING)
    with st.expander("🛠️ Raw JSON Response (Developer View)", expanded=False):
        st.json(result_dict)
