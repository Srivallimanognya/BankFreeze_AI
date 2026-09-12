"""
Escalation View for BankFreeze AI
Implements demonstration 3-tier escalation workflow:
Level 1 (Branch / IO) -> Level 2 (Nodal / Ombudsman) -> Level 3 (Legal / Courts).
"""

import streamlit as st
from datetime import datetime
from sqlalchemy.orm import Session

from database.models import Case, Escalation
from modules.escalation import escalation_engine
from modules.audit import log_audit
from ui.components import render_status_badge

def render_escalation_view(db: Session, case_id: str):
    st.markdown("## 🚨 Multi-Tier Escalation Workflow")
    st.caption("Demonstration workflow engine tracking response windows and recommending escalating legal/nodal channels.")

    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        st.error("Case not found.")
        return

    # Check active escalation record
    current_esc = db.query(Escalation).filter(Escalation.case_id == case_id).first()
    active_level = current_esc.level if current_esc else "LEVEL_1"

    # Evaluate readiness
    readiness = escalation_engine.evaluate_escalation_readiness(
        case_status=case.status,
        initial_comm_date=case.created_at,
        current_escalation_level=active_level,
        has_response=(case.status == "INFORMATION_RECEIVED")
    )

    # 3-Tier Visualizer
    st.markdown("### 🪜 Escalation Pathway Architecture")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        is_active = active_level == "LEVEL_1"
        border_color = "#3b82f6" if is_active else "#e2e8f0"
        st.markdown(f"""
        <div style="background: #ffffff; border: 2px solid {border_color}; border-radius: 8px; padding: 14px; height: 100%;">
            <div style="display: flex; justify-content: space-between;">
                <strong>LEVEL 1</strong>
                {'<span class="badge badge-info">CURRENT</span>' if is_active else ''}
            </div>
            <h4 style="margin: 6px 0; color: #0f172a;">Case-Handling Channel</h4>
            <p style="font-size: 0.82rem; color: #64748b;">
                Initial factual submission to Branch Manager and primary Investigating Officer (IO).
            </p>
            <span style="font-size: 0.78rem; font-weight: 600; color: #475569;">Wait Window: 7 Business Days</span>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        is_active = active_level == "LEVEL_2"
        border_color = "#3b82f6" if is_active else "#e2e8f0"
        st.markdown(f"""
        <div style="background: #ffffff; border: 2px solid {border_color}; border-radius: 8px; padding: 14px; height: 100%;">
            <div style="display: flex; justify-content: space-between;">
                <strong>LEVEL 2</strong>
                {'<span class="badge badge-warning">CURRENT</span>' if is_active else ''}
            </div>
            <h4 style="margin: 6px 0; color: #0f172a;">Official Grievance / Nodal</h4>
            <p style="font-size: 0.82rem; color: #64748b;">
                Formal escalation to Principal Nodal Officer, Cyber Cell ACP/DCP, or RBI Banking Ombudsman.
            </p>
            <span style="font-size: 0.78rem; font-weight: 600; color: #475569;">Wait Window: 14 Business Days</span>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        is_active = active_level == "LEVEL_3"
        border_color = "#ef4444" if is_active else "#e2e8f0"
        st.markdown(f"""
        <div style="background: #ffffff; border: 2px solid {border_color}; border-radius: 8px; padding: 14px; height: 100%;">
            <div style="display: flex; justify-content: space-between;">
                <strong>LEVEL 3</strong>
                {'<span class="badge badge-danger">CURRENT</span>' if is_active else ''}
            </div>
            <h4 style="margin: 6px 0; color: #0f172a;">Judicial / Legal Assistance</h4>
            <p style="font-size: 0.82rem; color: #64748b;">
                Advocate representation for de-freezing order under Sec 451/457 CrPC or High Court Writ.
            </p>
            <span style="font-size: 0.78rem; font-weight: 600; color: #475569;">Window: 30+ Days / Immediate</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Readiness & Recommendation Panel
    st.markdown("### 🧭 Escalation Readiness Assessment")
    st.markdown(f"""
    <div style="background: #f8fafc; border-left: 4px solid #3b82f6; padding: 16px; border-radius: 4px; margin-bottom: 20px;">
        <div style="font-size: 0.85rem; color: #64748b; font-weight: 700; text-transform: uppercase;">
            Engine Recommendation ({readiness['badge']})
        </div>
        <div style="font-size: 1.05rem; color: #1e293b; font-weight: 600; margin: 6px 0;">
            {readiness['recommendation']}
        </div>
        <div style="font-size: 0.85rem; color: #475569;">
            Elapsed since intake: <strong>{readiness['days_elapsed']} days</strong> | 
            Standard tier threshold: <strong>{readiness['threshold_days']} days</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Escalation Action Controls
    st.markdown("### ⚡ Execute Demonstration Escalation Step")
    col_t, col_btn = st.columns([3, 1])
    with col_t:
        target_step = st.selectbox(
            "Select Escalation Target to Enact:",
            [
                "LEVEL_1: Reinforce Branch Operations Representation",
                "LEVEL_2: Escalate to Principal Nodal Officer / Cyber In-Charge",
                "LEVEL_3: Recommend Independent Legal Counsel / Court Bond"
            ]
        )
    with col_btn:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("Trigger Escalation ➔", use_container_width=True):
            new_lvl = target_step.split(":")[0].strip()
            if not current_esc:
                current_esc = Escalation(
                    case_id=case_id,
                    level=new_lvl,
                    reason=f"Manual/automated transition triggered in UI to {new_lvl}",
                    channel=target_step,
                    status="IN_PROGRESS"
                )
                db.add(current_esc)
            else:
                current_esc.level = new_lvl
                current_esc.channel = target_step
                current_esc.status = "IN_PROGRESS"

            case.status = "ESCALATION_REQUIRED"
            log_audit(
                db,
                action="TRANSITION_ESCALATION_TIER",
                actor="USER",
                case_id=case_id,
                result="SUCCESS",
                details={"tier": new_lvl, "channel": target_step}
            )
            db.commit()
            st.success(f"Case escalated to {new_lvl} successfully!")
            st.rerun()
