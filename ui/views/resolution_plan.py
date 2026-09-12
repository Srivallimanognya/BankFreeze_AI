"""
Resolution Plan View for BankFreeze AI
Exhibits the Resolution Agent's autonomous reasoning:
- What is known?
- What is unknown?
- What conflicts exist?
- Who should be contacted?
- What documents should be prepared?
- Actionable task manager with completion status.
"""

import streamlit as st
from sqlalchemy.orm import Session

from database.models import Case, Task
from modules.resolution_agent import ResolutionAgent
from modules.audit import log_audit
from ui.components import render_status_badge

def render_resolution_plan(db: Session, case_id: str):
    st.markdown("## 📋 Autonomous Resolution Strategy & Action Plan")
    st.caption("Agentic synthesis of verified facts, investigative gaps, respondent directory, and resolution tasks.")

    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        st.error("Case not found.")
        return

    agent = ResolutionAgent(db)
    reasoning = agent.reason_and_synthesize(case_id)

    # Prominent Safety Notice
    st.markdown(f"""
    <div style="background-color: #f1f5f9; border-left: 4px solid #475569; padding: 10px 14px; font-size: 0.85rem; color: #334155; margin-bottom: 15px;">
        🛡️ <strong>AGENTIC SAFETY PRINCIPLE:</strong> {reasoning['guardrail_notice']}
    </div>
    """, unsafe_allow_html=True)

    # Knowns vs Unknowns
    c_known, c_unknown = st.columns(2)
    with c_known:
        st.markdown("### 🟢 What is Verified / Known")
        for item in reasoning["knowns"]:
            st.markdown(f"- ✅ {item}")

    with c_unknown:
        st.markdown("### 🟡 What is Missing / Unknown")
        if not reasoning["unknowns"]:
            st.markdown("- *All primary factual parameters identified.*")
        else:
            for item in reasoning["unknowns"]:
                st.markdown(f"- ❓ {item}")

    st.divider()

    # Contacts & Document Prep
    col_dir, col_docs = st.columns(2)
    with col_dir:
        st.markdown("### 📞 Designated Communication Targets")
        for target in reasoning["contact_targets"]:
            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px;">
                <div style="font-weight: 700; color: #0f172a;">{target['target']}</div>
                <div style="font-size: 0.8rem; color: #3b82f6; font-weight: 600;">Role: {target['role']}</div>
                <div style="font-size: 0.82rem; color: #64748b; margin-top: 2px;">{target['purpose']}</div>
            </div>
            """, unsafe_allow_html=True)

    with col_docs:
        st.markdown("### 📁 Prescribed Document Dossier")
        for doc_item in reasoning["documents_to_prepare"]:
            st.markdown(f"- 📄 {doc_item}")

    st.divider()

    # Recommended Procedural Sequence
    st.markdown("### 🎯 Recommended Strategic Steps")
    for idx, act in enumerate(reasoning["recommended_actions"], 1):
        st.markdown(f"**Step {idx}:** {act}")

    st.divider()

    # Actionable Task Manager
    st.markdown("### 📌 Case Action Checklist & Tasks")
    tasks = db.query(Task).filter(Task.case_id == case_id).all()
    
    if not tasks:
        st.caption("No specific tasks generated yet.")
    else:
        for t in tasks:
            c_chk, c_txt = st.columns([1, 10])
            with c_chk:
                is_done = t.status == "COMPLETED"
                chk = st.checkbox("", value=is_done, key=f"task_chk_{t.task_id}")
                if chk != is_done:
                    t.status = "COMPLETED" if chk else "PENDING"
                    log_audit(db, action="UPDATE_TASK_STATUS", actor="USER", case_id=case_id, details={"task": t.title, "status": t.status})
                    db.commit()
                    st.rerun()
            with c_txt:
                st.markdown(f"**{t.title}** ({render_status_badge(t.status)})", unsafe_allow_html=True)
                if t.description:
                    st.caption(t.description)

    # Quick create task form
    with st.expander("➕ **Add Custom Action Task**"):
        with st.form(f"new_task_form_{case_id}"):
            t_title = st.text_input("Task Title *", placeholder="e.g., Obtain stamp on 6-month statement from branch")
            t_desc = st.text_area("Task Particulars", placeholder="Detailed instructions for the account holder or investigator", height=70)
            if st.form_submit_button("Add Task ➔"):
                if t_title:
                    agent.create_task(case_id, t_title, t_desc)
                    st.success("Task added!")
                    st.rerun()
