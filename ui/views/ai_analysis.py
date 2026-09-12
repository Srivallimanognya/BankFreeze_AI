"""
AI Analysis View for BankFreeze AI
Runs freeze categorization, evidentiary reasoning, and legal statutory pathways.
"""

import streamlit as st
from sqlalchemy.orm import Session

from database.models import Case, Document, Transaction, Authority
from modules.freeze_analyzer import freeze_analyzer
from modules.bank_adapter import MockBankAdapter
from modules.document_analyzer import document_analyzer
from ui.components import render_status_badge, render_confidence_badge

CATEGORY_LEGAL_GUIDANCE = {
    "COURT_ORDER": {
        "statute": "Section 91 & Section 102 Code of Criminal Procedure (Cr.P.C.)",
        "description": "Judicial attachment ordered by a Court of Law. The bank cannot de-freeze without an express judicial order.",
        "pathway": "File a formal interim application under Section 451 / 457 Cr.P.C. or a Writ Petition before the High Court under Article 226 for modification to lien."
    },
    "CYBERCRIME_COMPLAINT": {
        "statute": "National Cyber Crime Reporting Portal (NCRRP / 1930) / IT Act, 2000",
        "description": "Notice triggered by citizen fraud alert on helpline 1930. Often involves layered fund flow inquiries across multiple bank hops.",
        "pathway": "Submit certified bank statement and commercial trade proofs (invoices, P2P order receipts) to the Investigating Officer (IO) requesting release or limiting hold strictly to disputed lien."
    },
    "POLICE_REQUEST": {
        "statute": "Section 91 Cr.P.C. / State Police Cyber Cell Requisition",
        "description": "Police requisition requesting transaction hold pending preliminary enquiry.",
        "pathway": "Submit written representation directly to the investigating station in-charge and Bank Nodal Officer."
    },
    "KYC_RELATED": {
        "statute": "RBI Master Direction - Know Your Customer (KYC) Direction, 2016",
        "description": "Operational suspension due to failure in completing periodic Re-KYC verification.",
        "pathway": "Visit home branch with original Officially Valid Documents (OVDs: Aadhaar, PAN) and latest proof of address for immediate biometric / video in-person verification."
    },
    "AML_RELATED": {
        "statute": "Prevention of Money Laundering Act (PMLA) / FIU-IND Guidelines",
        "description": "Internal transaction monitoring alert triggered by sudden volume or velocity spikes.",
        "pathway": "Furnish income tax returns, audited balance sheets, or contracts establishing legitimate economic rationale."
    },
    "DISPUTED_TRANSACTION": {
        "statute": "NPCI / RBI Dispute & Chargeback Framework",
        "description": "Commercial dispute or chargeback initiated by payment gateway / counterparty bank.",
        "pathway": "Lodge merchant dispute response with delivery confirmation and mutual chat transcript."
    },
    "UNKNOWN": {
        "statute": "Unspecified Administrative Hold",
        "description": "Hold reason not disclosed or conflicting across notices.",
        "pathway": "Dispatch formal clarification notice to Bank Principal Nodal Officer seeking copy of regulatory notice."
    }
}

def render_ai_analysis(db: Session, case_id: str):
    st.markdown("## 🔍 AI Freeze Classification & Legal Basis")
    st.caption("Forensic assessment of the restriction type, statutory foundation, and legal remedies.")

    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        st.error("Case not found.")
        return

    docs = db.query(Document).filter(Document.case_id == case_id).all()
    doc_res = None
    if docs:
        doc_res = document_analyzer.analyze_document(docs[0].extracted_text or "", docs[0].filename)

    bank_adapter = MockBankAdapter()
    bank_freeze_details = bank_adapter.get_freeze_details(case.case_id)

    # Perform Classification
    res = freeze_analyzer.classify(
        stated_reason=case.freeze_reason,
        document_result=doc_res,
        bank_freeze_details=bank_freeze_details
    )

    # Classification Result Banner
    st.markdown(f"""
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 0.8rem; color: #64748b; font-weight: 700; text-transform: uppercase;">Classified Legal Category</span>
                <h2 style="margin: 4px 0; color: #1e293b;">{res.category.value}</h2>
            </div>
            <div>
                {render_confidence_badge(res.confidence.value)}
            </div>
        </div>
        <p style="margin-top: 8px; margin-bottom: 0; color: #475569; font-size: 0.95rem;">
            <strong>Evidentiary Basis:</strong> {res.evidence}
        </p>
        <span style="font-size: 0.78rem; color: #94a3b8;">Source Attribution: {res.source}</span>
    </div>
    """, unsafe_allow_html=True)

    # Statutory Pathway Guidance
    guidance = CATEGORY_LEGAL_GUIDANCE.get(res.category.value, CATEGORY_LEGAL_GUIDANCE["UNKNOWN"])
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ⚖️ Statutory Governance")
        st.info(f"**Applicable Legal Framework:**\n\n{guidance['statute']}")
        st.markdown(f"**Legal Context:**\n\n{guidance['description']}")

    with col2:
        st.markdown("### 🛠️ Procedural Resolution Pathway")
        st.success(f"**Recommended Strategic Next Step:**\n\n{guidance['pathway']}")
        st.caption("Note: Recommendations are procedural and require case officer verification.")

    st.divider()

    # Fact Extraction Diagnostics
    with st.expander("📊 **View Multi-Source Diagnostic Signals**"):
        st.markdown(f"- **User Stated Reason:** {case.freeze_reason}")
        if bank_freeze_details:
            st.markdown(f"- **Bank Core Reason:** {bank_freeze_details.get('reason')} (Authority: {bank_freeze_details.get('requesting_authority')})")
        if doc_res:
            st.markdown(f"- **Notice Document Detected Category:** {doc_res.document_type} (Ref: {doc_res.reference_number.value})")
