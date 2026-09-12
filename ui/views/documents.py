"""
Documents View for BankFreeze AI
Supports upload of PDF, PNG, JPG, TXT notices and exhibits structured facts
with strict confidence ratings and anti-hallucination indicators.
"""

import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.models import Case, Document, Authority, Transaction
from modules.document_analyzer import document_analyzer
from modules.audit import log_audit
from ui.components import render_confidence_badge, render_fact_badge
from schemas.case import FactType

def render_documents(db: Session, case_id: str):
    st.markdown("## 📄 Document Repository & Forensic Extraction")
    st.caption("Upload freeze intimations, police notices, or court orders to extract verifiable facts without hallucination.")

    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        st.error("Case not found.")
        return

    # Document Uploader
    with st.expander("📤 **Upload New Document (PDF, TXT, PNG, JPG)**", expanded=True):
        uploaded_file = st.file_uploader(
            "Select notice or exhibit",
            type=["pdf", "txt", "png", "jpg", "jpeg"],
            key="doc_uploader_main"
        )
        if uploaded_file is not None:
            if st.button("Process & Extract Document Facts ➔", use_container_width=True):
                file_bytes = uploaded_file.read()
                raw_text = document_analyzer.extract_text_from_file(file_bytes, uploaded_file.name)
                
                # Analyze text
                res = document_analyzer.analyze_document(raw_text, uploaded_file.name)
                
                # Store document
                doc = Document(
                    case_id=case_id,
                    filename=uploaded_file.name,
                    document_type=res.document_type,
                    extracted_text=raw_text,
                    metadata_json=res.model_dump_json()
                )
                db.add(doc)
                
                # If authority was extracted and no authority currently exists, update case authority
                if res.authority.fact_type != FactType.MISSING and res.reference_number.fact_type != FactType.MISSING:
                    existing_auth = db.query(Authority).filter(Authority.case_id == case_id).first()
                    if not existing_auth:
                        new_auth = Authority(
                            case_id=case_id,
                            authority_name=res.authority.value,
                            jurisdiction=res.jurisdiction.value if res.jurisdiction.fact_type != FactType.MISSING else "NOT SPECIFIED",
                            reference_number=res.reference_number.value,
                            officer_name=res.officer_name.value if res.officer_name.fact_type != FactType.MISSING else "NOT PROVIDED",
                            contact_information=res.contact_information.value if res.contact_information.fact_type != FactType.MISSING else "NOT PROVIDED",
                            source=f"Uploaded Document ({uploaded_file.name})",
                            confidence=res.authority.confidence.value
                        )
                        db.add(new_auth)

                log_audit(
                    db,
                    action="UPLOAD_AND_ANALYZE_DOCUMENT",
                    actor="USER",
                    case_id=case_id,
                    result="SUCCESS",
                    details={"filename": uploaded_file.name, "doc_type": res.document_type}
                )
                db.commit()
                st.success(f"Document `{uploaded_file.name}` processed and facts extracted!")
                st.rerun()

    st.divider()

    # Existing Documents List
    docs = db.query(Document).filter(Document.case_id == case_id).all()
    if not docs:
        st.info("No documents are currently linked to this case.")
        return

    st.markdown("### 📑 Attached Case Documents & Extracted Facts")
    for doc in docs:
        with st.container():
            st.markdown(f"#### 📎 {doc.filename} `[{doc.document_type}]`")
            st.caption(f"Uploaded: {doc.uploaded_at.strftime('%Y-%m-%d %H:%M UTC')}")
            
            # Re-run or parse structured extraction
            extraction_res = document_analyzer.analyze_document(doc.extracted_text or "", doc.filename)
            
            # Facts Display Grid
            facts_list = [
                ("Freeze Reason", extraction_res.freeze_reason),
                ("Restriction Type", extraction_res.restriction_type),
                ("Transaction ID", extraction_res.transaction_id),
                ("Disputed Amount", extraction_res.amount),
                ("Transaction Date", extraction_res.transaction_date),
                ("Requesting Authority", extraction_res.authority),
                ("Jurisdiction", extraction_res.jurisdiction),
                ("Reference Number", extraction_res.reference_number),
                ("Complaint Number", extraction_res.complaint_number),
                ("Order Number", extraction_res.order_number),
                ("Officer Name", extraction_res.officer_name),
                ("Contact Information", extraction_res.contact_information),
            ]

            # Render structured facts table with HTML chips
            rows_html = []
            for field_name, fact in facts_list:
                conf_chip = render_confidence_badge(fact.confidence.value)
                type_chip = render_fact_badge(fact.fact_type.value)
                val_display = f"<strong>{fact.value}</strong>" if fact.fact_type.value != "MISSING" else f"<em>{fact.value}</em>"
                rows_html.append(f"""
                <tr>
                    <td style="padding: 6px 12px; font-weight: 600;">{field_name}</td>
                    <td style="padding: 6px 12px;">{val_display}</td>
                    <td style="padding: 6px 12px; font-size: 0.8rem; color: #64748b;">{fact.source}</td>
                    <td style="padding: 6px 12px;">{conf_chip}</td>
                    <td style="padding: 6px 12px;">{type_chip}</td>
                </tr>
                """)

            table_html = f"""
            <table style="width: 100%; border-collapse: collapse; font-size: 0.88rem; margin-top: 8px; margin-bottom: 12px;">
                <thead>
                    <tr style="background-color: #f8fafc; border-bottom: 2px solid #e2e8f0; text-align: left;">
                        <th style="padding: 8px 12px;">Target Field</th>
                        <th style="padding: 8px 12px;">Extracted Value</th>
                        <th style="padding: 8px 12px;">Source Attribution</th>
                        <th style="padding: 8px 12px;">Confidence</th>
                        <th style="padding: 8px 12px;">Fact Status</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows_html)}
                </tbody>
            </table>
            """
            st.markdown(table_html, unsafe_allow_html=True)

            # Missing Facts Summary
            if extraction_res.missing_fields:
                missing_labels = [f.replace("_", " ").title() for f in extraction_res.missing_fields]
                st.warning(f"⚠️ **Information Not Available in Submitted Document:** {', '.join(missing_labels)}")

            with st.expander("🔍 View Raw Extracted Text"):
                st.text_area("Raw Text", doc.extracted_text or "", height=150, disabled=True, key=f"raw_text_view_{doc.document_id}")
            
            st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
