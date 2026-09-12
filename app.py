"""
BankFreeze AI - Main Streamlit Application Entry Point
Agentic AI-Based Bank Account Freeze Investigation, Resolution and Escalation System
"""

import streamlit as st
from database.connection import init_db, SessionLocal
from database.models import Case
from demo.seed_data import seed_database
from ui.components import inject_custom_css, render_disclaimer, render_status_badge

# Import view components
from ui.views.dashboard import render_dashboard
from ui.views.create_case import render_create_case
from ui.views.case_details import render_case_details
from ui.views.documents import render_documents
from ui.views.ai_analysis import render_ai_analysis
from ui.views.transactions import render_transactions
from ui.views.authority_info import render_authority_info
from ui.views.reconciliation_view import render_reconciliation_view
from ui.views.resolution_plan import render_resolution_plan
from ui.views.communications import render_communications
from ui.views.escalation_view import render_escalation_view
from ui.views.audit_log_view import render_audit_log_view
from ui.views.settings_view import render_settings_view
from ui.views.workflow_view import render_workflow_view

# Configure Streamlit page
st.set_page_config(
    page_title="BankFreeze AI - Case Resolution System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject styling and setup DB
inject_custom_css()
init_db()

# Ensure seed data exists
try:
    seed_database()
except Exception:
    pass

def main():
    db = SessionLocal()
    try:
        # Mandatory top disclaimer banner
        render_disclaimer()

        # Session state initialization
        if "active_page" not in st.session_state:
            st.session_state["active_page"] = "Dashboard"

        # Fetch cases for sidebar selector deterministically
        all_cases = db.query(Case).order_by(Case.case_id.asc()).all()
        case_lookup = {c.case_id: c for c in all_cases}

        if "selected_case_id" not in st.session_state or st.session_state["selected_case_id"] not in case_lookup:
            st.session_state["selected_case_id"] = all_cases[0].case_id if all_cases else None

        # Sidebar Navigation
        with st.sidebar:
            st.markdown("## 🛡️ **BANKFREEZE AI**")
            st.caption("Agentic Account Freeze Investigation & Resolution System")
            st.markdown("<hr style='margin: 8px 0;'>", unsafe_allow_html=True)

            # Active Case Context Selector
            st.markdown("##### 🎯 Active Investigation Case")
            if all_cases:
                case_ids = [c.case_id for c in all_cases]
                curr_selected = st.session_state.get("selected_case_id")
                default_idx = case_ids.index(curr_selected) if curr_selected in case_ids else 0

                def _on_sidebar_case_change():
                    st.session_state["selected_case_id"] = st.session_state["sidebar_case_selector"]

                selected_id = st.selectbox(
                    "Switch Active Case:",
                    case_ids,
                    index=default_idx,
                    format_func=lambda cid: f"{cid} - {case_lookup[cid].bank_name} ({case_lookup[cid].masked_account_number})",
                    key="sidebar_case_selector",
                    on_change=_on_sidebar_case_change,
                    label_visibility="collapsed"
                )
                st.session_state["selected_case_id"] = selected_id

                # Quick active case summary card
                curr_c = db.query(Case).filter(Case.case_id == st.session_state["selected_case_id"]).first()
                if curr_c:
                    st.markdown(f"""
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 12px; margin-top: 6px; font-size: 0.8rem;">
                        <strong>Status:</strong> {render_status_badge(curr_c.status)}<br>
                        <strong>Type:</strong> <code>{curr_c.restriction_type}</code><br>
                        <strong>Bank:</strong> {curr_c.bank_name}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No cases available. Please create one.")

            st.markdown("<hr style='margin: 12px 0;'>", unsafe_allow_html=True)

            # Navigation Menu Items
            menu_options = [
                "📊 Dashboard",
                "➕ Create Case",
                "📁 Case Details",
                "📄 Documents",
                "🔍 AI Analysis",
                "💳 Transactions",
                "🏛️ Authority Information",
                "⚖️ Multi-Source Reconciliation",
                "📋 Resolution Plan",
                "✉️ Communications",
                "🚨 Escalation",
                "📜 Audit Log",
                "🔗 n8n Workflow",
                "⚙️ Settings"
            ]

            # Match active_page to menu index
            default_menu_idx = 0
            for idx, opt in enumerate(menu_options):
                clean_opt = opt.split(" ", 1)[1]
                if clean_opt == st.session_state["active_page"]:
                    default_menu_idx = idx
                    break

            selected_nav = st.radio(
                "Navigation Menu",
                menu_options,
                index=default_menu_idx,
                label_visibility="collapsed"
            )
            # Update state if changed by click
            selected_page_name = selected_nav.split(" ", 1)[1]
            if selected_page_name != st.session_state["active_page"]:
                st.session_state["active_page"] = selected_page_name
                st.rerun()

            st.markdown("<hr style='margin: 12px 0;'>", unsafe_allow_html=True)
            st.caption("🔒 Architecture Guardrail: Mock Isolation Active. Real Banking APIs Disconnected.")

        # Main Page Dispatcher
        active_page = st.session_state["active_page"]
        active_case_id = st.session_state.get("selected_case_id")

        if active_page == "Dashboard":
            render_dashboard(db)
        elif active_page == "Create Case":
            render_create_case(db)
        elif active_page == "Case Details":
            if active_case_id:
                render_case_details(db, active_case_id)
            else:
                st.warning("Please select or create a case first.")
        elif active_page == "Documents":
            if active_case_id:
                render_documents(db, active_case_id)
            else:
                st.warning("Please select or create a case first.")
        elif active_page == "AI Analysis":
            if active_case_id:
                render_ai_analysis(db, active_case_id)
            else:
                st.warning("Please select or create a case first.")
        elif active_page == "Transactions":
            if active_case_id:
                render_transactions(db, active_case_id)
            else:
                st.warning("Please select or create a case first.")
        elif active_page == "Authority Information":
            if active_case_id:
                render_authority_info(db, active_case_id)
            else:
                st.warning("Please select or create a case first.")
        elif active_page == "Multi-Source Reconciliation":
            if active_case_id:
                render_reconciliation_view(db, active_case_id)
            else:
                st.warning("Please select or create a case first.")
        elif active_page == "Resolution Plan":
            if active_case_id:
                render_resolution_plan(db, active_case_id)
            else:
                st.warning("Please select or create a case first.")
        elif active_page == "Communications":
            if active_case_id:
                render_communications(db, active_case_id)
            else:
                st.warning("Please select or create a case first.")
        elif active_page == "Escalation":
            if active_case_id:
                render_escalation_view(db, active_case_id)
            else:
                st.warning("Please select or create a case first.")
        elif active_page == "Audit Log":
            render_audit_log_view(db, active_case_id)
        elif active_page == "n8n Workflow":
            render_workflow_view(db, active_case_id)
        elif active_page == "Settings":
            render_settings_view(db)
        else:
            st.error(f"Unknown page: {active_page}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
