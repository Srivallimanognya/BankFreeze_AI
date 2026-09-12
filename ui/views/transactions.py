"""
Transactions View for BankFreeze AI
Displays flagged or disputed transactions and provides tools to append transaction entries.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

from database.models import Case, Transaction
from modules.audit import log_audit
from ui.components import render_status_badge

def render_transactions(db: Session, case_id: str):
    st.markdown("## 💳 Disputed & Flagged Transactions Ledger")
    st.caption("Review transactions associated with freeze requisitions, lien markers, or counterparty disputes.")

    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        st.error("Case not found.")
        return

    txns = db.query(Transaction).filter(Transaction.case_id == case_id).all()

    if not txns:
        st.info("No transaction records registered for this case yet.")
    else:
        table_rows = []
        for t in txns:
            table_rows.append({
                "Transaction ID": t.transaction_id,
                "Amount (₹)": f"₹{t.amount:,.2f}",
                "Date": t.transaction_date.strftime("%Y-%m-%d"),
                "Dispute Status": t.dispute_status,
                "Source": t.source,
                "Description": t.description or "No description"
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    st.divider()

    # Form to add additional transaction
    with st.expander("➕ **Add Associated Transaction Entry**", expanded=False):
        with st.form("add_txn_form"):
            c1, c2 = st.columns(2)
            with c1:
                new_txn_id = st.text_input("Transaction ID / UTR *", placeholder="e.g., TXN-2025-XXXX or UPI/99812")
                new_amt = st.number_input("Amount (₹) *", min_value=1.0, step=100.0, value=1000.0)
            with c2:
                new_date = st.date_input("Transaction Date *", value=datetime.today())
                new_status = st.selectbox("Dispute Status", ["DISPUTED", "FLAGGED", "CLEARED", "UNKNOWN"])

            new_source = st.selectbox("Information Source", ["USER_STATEMENT", "BANK_ADAPTER", "NOTICE_DOC"])
            new_desc = st.text_input("Transaction Note / Description", placeholder="e.g., Immediate IMPS transfer from counterparty")

            submit_txn = st.form_submit_button("Record Transaction ➔")
            if submit_txn:
                if not new_txn_id:
                    st.error("Transaction ID is required.")
                else:
                    t_entry = Transaction(
                        transaction_id=new_txn_id.strip(),
                        case_id=case_id,
                        amount=new_amt,
                        transaction_date=datetime.combine(new_date, datetime.min.time()),
                        dispute_status=new_status,
                        source=new_source,
                        description=new_desc
                    )
                    db.add(t_entry)
                    log_audit(db, action="ADD_CASE_TRANSACTION", actor="USER", case_id=case_id, details={"txn_id": new_txn_id, "amount": new_amt})
                    db.commit()
                    st.success(f"Transaction `{new_txn_id}` added to case!")
                    st.rerun()
