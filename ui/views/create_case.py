"""
Create Case View for BankFreeze AI
Provides intake form with input validation, real-time account masking,
prohibited credential filtering (OTP/PIN/CVV blocks), and initial notice ingestion.
"""

import streamlit as st
from datetime import datetime
from sqlalchemy.orm import Session

from database.models import Case, Transaction, Document, User
from modules.security import mask_account_number, detect_prohibited_credentials
from modules.audit import log_audit
from modules.document_analyzer import document_analyzer
from schemas.case import RestrictionType, CaseStatus

def render_create_case(db: Session):
    st.markdown("## ➕ Intake: Register New Freeze Investigation Case")
    st.caption("Submit basic bank account details and preliminary freeze notices to initiate autonomous investigation.")

    with st.form("create_case_form"):
        col1, col2 = st.columns(2)
        with col1:
            bank_name = st.text_input("Bank Name *", placeholder="e.g., State Bank of India, HDFC Bank, ICICI Bank")
            raw_acc = st.text_input("Account Number *", placeholder="e.g., 123456789012")
            if raw_acc:
                st.caption(f"🔒 Account Mask Preview: **{mask_account_number(raw_acc)}**")

            freeze_date = st.date_input("Date Restriction Was Observed *", value=datetime.today())

        with col2:
            restriction_type = st.selectbox(
                "Observed Restriction Type *",
                [r.value for r in RestrictionType],
                index=1
            )
            disputed_amount = st.number_input("Disputed Amount (₹) if known", min_value=0.0, step=500.0, value=0.0)
            transaction_id = st.text_input("Disputed Transaction Reference / UTR (if known)", placeholder="e.g., TXN-DEMO-001 or UPI/123456")

        freeze_reason = st.text_area(
            "Stated Freeze Reason *",
            placeholder="Describe what the bank or SMS notification stated (e.g. 'Account debits blocked as per cyber cell order')",
            height=80
        )
        user_narrative = st.text_area(
            "Account Holder Narrative / Context",
            placeholder="Explain background (e.g. 'I sold merchandise online and received payment; counterparty filed false dispute')",
            height=100
        )

        st.markdown("##### 📄 Upload Initial Freeze Notice / Bank Intimation (Optional)")
        uploaded_file = st.file_uploader("Upload PDF, TXT, PNG, or JPG", type=["pdf", "txt", "png", "jpg", "jpeg"])

        submitted = st.form_submit_button("Initiate Case Investigation ➔", use_container_width=True)

        if submitted:
            # 1. Validation
            if not bank_name or not raw_acc or not freeze_reason:
                st.error("Please fill all required fields marked with *.")
                return

            # 2. Strict Security Check: Forbid OTP, UPI PIN, CVV, ATM PIN
            combined_text = f"{freeze_reason} {user_narrative}"
            has_forbidden, forbidden_terms = detect_prohibited_credentials(combined_text)
            if has_forbidden:
                st.error(
                    f"⛔ SECURITY ALERT: Prohibited sensitive credential terms detected: {', '.join(forbidden_terms)}. "
                    "For your security, NEVER enter OTPs, CVVs, ATM PINs, or UPI PINs into the application."
                )
                return

            # 3. Create Case Record
            masked_acc = mask_account_number(raw_acc)
            case_count = db.query(Case).count()
            case_id = f"CASE-{datetime.utcnow().strftime('%Y')}-{case_count + 1:04d}"

            # Fetch or use default demo user
            demo_user = db.query(User).first()
            user_id = demo_user.user_id if demo_user else "USER-DEMO-001"

            new_case = Case(
                case_id=case_id,
                user_id=user_id,
                bank_name=bank_name.strip(),
                masked_account_number=masked_acc,
                freeze_date=datetime.combine(freeze_date, datetime.min.time()),
                restriction_type=restriction_type,
                freeze_reason=freeze_reason.strip(),
                status=CaseStatus.NEW.value,
                metadata_json=f'{{"narrative": "{user_narrative}"}}'
            )
            db.add(new_case)
            db.flush()

            # 4. If transaction details provided, record Transaction
            if transaction_id and transaction_id.strip():
                txn = Transaction(
                    transaction_id=transaction_id.strip(),
                    case_id=case_id,
                    amount=disputed_amount,
                    transaction_date=datetime.combine(freeze_date, datetime.min.time()),
                    dispute_status="DISPUTED",
                    source="USER_INTAKE",
                    description="Reported by user during initial intake"
                )
                db.add(txn)

            # 5. If document uploaded, extract and store
            if uploaded_file:
                file_bytes = uploaded_file.read()
                raw_text = document_analyzer.extract_text_from_file(file_bytes, uploaded_file.name)
                doc = Document(
                    case_id=case_id,
                    filename=uploaded_file.name,
                    document_type="INITIAL_NOTICE",
                    extracted_text=raw_text
                )
                db.add(doc)

            # 6. Audit Logging
            log_audit(
                db,
                action="CREATE_CASE_INTAKE",
                actor="USER",
                case_id=case_id,
                result="SUCCESS",
                details={"bank": bank_name, "account": masked_acc, "restriction_type": restriction_type}
            )

            db.commit()

            st.success(f"Case {case_id} registered successfully! Directing to Case Dossier...")
            st.session_state["selected_case_id"] = case_id
            st.session_state["active_page"] = "Case Details"
            st.rerun()
