"""
Communications & Human Approval View for BankFreeze AI
Implements strict Human-in-the-Loop approval workflow:
AI generates draft -> USER REVIEWS -> USER EDITS -> USER APPROVES -> SYSTEM RECORDS.
Provides APPROVE, EDIT, and REJECT actions with immutable audit trail.
"""

from datetime import datetime
import streamlit as st
from sqlalchemy.orm import Session

from database.models import Case, Communication
from modules.resolution_agent import ResolutionAgent
from modules.audit import log_audit
from ui.components import render_status_badge

def render_communications(db: Session, case_id: str):
    st.markdown("## ✉️ Draft Representations & Human Approval Gate")
    st.caption("Review, edit, and approve formal written submissions before they are finalized or dispatched.")

    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        st.error("Case not found.")
        return

    agent = ResolutionAgent(db)

    # Draft Generator Hub
    with st.expander("📝 **Generate New AI Communication Draft**", expanded=True):
        col_type, col_btn = st.columns([3, 1])
        with col_type:
            draft_type = st.selectbox(
                "Select Representation Category:",
                [
                    "Bank Clarification Request (To Branch / Nodal Officer)",
                    "Authority Clarification Submission (To Cyber Cell / Investigating Officer)",
                    "Status Follow-Up (To Nodal Desk after 7+ days)",
                    "Formal Grievance Escalation (Level 2 to Principal Nodal Officer / Ombudsman)"
                ]
            )
        with col_btn:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            gen_clicked = st.button("Generate Draft ➔", use_container_width=True)

        if gen_clicked:
            if "Bank" in draft_type:
                comm = agent.generate_inquiry(case_id, "BANK")
            elif "Authority" in draft_type:
                comm = agent.generate_inquiry(case_id, "AUTHORITY")
            elif "Follow-Up" in draft_type:
                comm = agent.generate_followup(case_id)
            else:
                comm = agent.generate_escalation(case_id, "LEVEL_2")

            st.success("AI draft prepared successfully! Review and approve below.")
            st.rerun()

    st.divider()

    # Active Communications Review Section
    comms = db.query(Communication).filter(Communication.case_id == case_id).order_by(Communication.created_at.desc()).all()
    if not comms:
        st.info("No drafts or communications generated yet for this case.")
        return

    st.markdown("### 📋 Communications Queue & Review Bench")

    for comm in comms:
        with st.container():
            st.markdown(f"#### 📄 Subject: {comm.subject}")
            st.markdown(
                f"**Recipient Category:** `{comm.recipient_type}` | "
                f"**Status:** {render_status_badge(comm.status)} | "
                f"**Version:** v{comm.version} | "
                f"**Created:** {comm.created_at.strftime('%Y-%m-%d %H:%M UTC')}",
                unsafe_allow_html=True
            )

            # Editable Draft Box
            edited_body = st.text_area(
                "Representation Body (Edit as needed prior to approval):",
                value=comm.body,
                height=240,
                key=f"comm_body_editor_{comm.communication_id}",
                disabled=(comm.status in ["APPROVED", "RECORDED"])
            )

            # Action Buttons Row
            if comm.status in ["DRAFT", "EDITED"]:
                btn_col1, btn_col2, btn_col3, _ = st.columns([1.2, 1.2, 1, 3])
                
                with btn_col1:
                    if st.button("✅ APPROVE & RECORD", key=f"btn_app_{comm.communication_id}", use_container_width=True):
                        comm.body = edited_body
                        comm.status = "APPROVED"
                        comm.approved_at = datetime.utcnow()
                        case.status = "APPROVED"
                        log_audit(
                            db,
                            action="HUMAN_APPROVE_COMMUNICATION",
                            actor="USER",
                            case_id=case_id,
                            result="SUCCESS",
                            details={"communication_id": comm.communication_id, "subject": comm.subject}
                        )
                        db.commit()
                        st.success("Draft APPROVED and permanently recorded in case dossier!")
                        st.rerun()

                with btn_col2:
                    if st.button("💾 SAVE EDITS", key=f"btn_save_{comm.communication_id}", use_container_width=True):
                        comm.body = edited_body
                        comm.status = "EDITED"
                        comm.version += 1
                        log_audit(
                            db,
                            action="EDIT_COMMUNICATION_DRAFT",
                            actor="USER",
                            case_id=case_id,
                            result="SUCCESS",
                            details={"communication_id": comm.communication_id, "version": comm.version}
                        )
                        db.commit()
                        st.info("Edits saved to draft!")
                        st.rerun()

                with btn_col3:
                    if st.button("❌ REJECT", key=f"btn_rej_{comm.communication_id}", use_container_width=True):
                        comm.status = "REJECTED"
                        log_audit(
                            db,
                            action="REJECT_COMMUNICATION_DRAFT",
                            actor="USER",
                            case_id=case_id,
                            result="BLOCKED",
                            details={"communication_id": comm.communication_id}
                        )
                        db.commit()
                        st.warning("Draft rejected and marked inactive.")
                        st.rerun()
            else:
                st.caption(f"🔒 Status locked: {comm.status}. Approved at: {comm.approved_at.strftime('%Y-%m-%d %H:%M UTC') if comm.approved_at else 'N/A'}")

            st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
