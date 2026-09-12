"""
Authority Information View for BankFreeze AI
Displays identified law-enforcement / statutory authority data, officer contacts,
and required documentary submissions retrieved via MockAuthorityAdapter.
"""

import streamlit as st
from sqlalchemy.orm import Session

from database.models import Case, Authority
from modules.authority_adapter import MockAuthorityAdapter
from modules.audit import log_audit
from ui.components import render_confidence_badge

def render_authority_info(db: Session, case_id: str):
    st.markdown("## 🏛️ Identified Law Enforcement & Statutory Authority")
    st.caption("Verifiable information regarding the requisitioning body, investigating officers, and formal contacts.")

    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        st.error("Case not found.")
        return

    auth = db.query(Authority).filter(Authority.case_id == case_id).first()
    auth_adapter = MockAuthorityAdapter()

    if not auth:
        st.warning("⚠️ No authority is formally linked to this case yet.")
        if st.button("Query Mock Authority Registry via Case ID ➔"):
            auth_info = auth_adapter.get_case_information("LEA-DEMO-001")
            new_auth = Authority(
                case_id=case_id,
                authority_name=auth_info.get("authority_name", "Cyber Crime Unit"),
                jurisdiction=auth_info.get("jurisdiction", "Telangana"),
                reference_number=auth_info.get("reference_number", "LEA-DEMO-001"),
                officer_name=auth_info.get("officer_name", "Investigating Officer"),
                contact_information=auth_info.get("contact_info", "cyber-demo@gov.in"),
                source="MOCK_AUTHORITY_ADAPTER",
                confidence="HIGH"
            )
            db.add(new_auth)
            log_audit(db, action="FETCH_MOCK_AUTHORITY_INFO", actor="AI_AGENT", case_id=case_id, details={"auth": new_auth.authority_name})
            db.commit()
            st.success("Authority information retrieved from Mock Registry!")
            st.rerun()
        return

    # Display Authority Card
    st.markdown(f"""
    <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0; color: #0f172a;">{auth.authority_name}</h3>
            {render_confidence_badge(auth.confidence)}
        </div>
        <p style="color: #64748b; font-size: 0.9rem; margin-top: 4px;">Jurisdiction: <strong>{auth.jurisdiction}</strong></p>
        <hr style="margin: 12px 0; border: 0; border-top: 1px solid #e2e8f0;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 0.9rem;">
            <div>
                <span style="color: #64748b;">Statutory Reference / Order No:</span><br>
                <code style="font-size: 0.95rem; font-weight: 700;">{auth.reference_number}</code>
            </div>
            <div>
                <span style="color: #64748b;">Assigned Officer:</span><br>
                <strong>{auth.officer_name or 'NOT PROVIDED'}</strong>
            </div>
            <div>
                <span style="color: #64748b;">Official Contact Information:</span><br>
                <strong>{auth.contact_information or 'NOT PROVIDED'}</strong>
            </div>
            <div>
                <span style="color: #64748b;">Information Source:</span><br>
                <span class="badge badge-neutral">{auth.source}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Query adapter for required document checklist
    st.markdown("### 📋 Statutory Requirements Checklist")
    case_query = auth_adapter.get_case_information(auth.reference_number)
    
    if case_query.get("found"):
        st.markdown(f"**Formal Allegation / Grounds:** *{case_query.get('allegation')}*")
        st.markdown("##### Documents Required for Consideration of Account Release:")
        req_docs = case_query.get("required_documents", [])
        for doc_item in req_docs:
            st.markdown(f"- ✅ **{doc_item}**")
    else:
        st.info("No specific checklist found in mock registry for this reference.")
