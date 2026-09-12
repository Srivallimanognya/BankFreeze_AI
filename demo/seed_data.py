"""
Seed Data Generator for BankFreeze AI
Creates 5 comprehensive, realistic synthetic demo cases with relational documents,
transactions, authorities, tasks, and audit logs.
All cases are explicitly labeled [DEMO DATA].
"""

from datetime import datetime, timedelta
from pathlib import Path
from database.connection import get_db, init_db
from database.models import User, Case, Document, Transaction, Authority, Communication, Task, Escalation, AuditLog
from modules.security import hash_password

SAMPLE_DOCS_DIR = Path(__file__).parent / "sample_documents"

def seed_database():
    init_db()
    with get_db() as db:
        # Check if already seeded
        existing_user = db.query(User).filter(User.username == "demo_user").first()
        if existing_user:
            return

        # 1. Create Demo User
        demo_user = User(
            user_id="USER-DEMO-001",
            username="demo_user",
            email="demo@bankfreeze.ai",
            password_hash=hash_password("DemoUser@2025"),
            role="COMPLIANCE_OFFICER"
        )
        db.add(demo_user)
        db.flush()

        # Helper to read sample document text
        def read_sample(filename: str) -> str:
            path = SAMPLE_DOCS_DIR / filename
            if path.exists():
                return path.read_text(encoding="utf-8")
            return f"[Sample text for {filename}]"

        # --- CASE 1: Disputed P2P Transaction ---
        c1 = Case(
            case_id="CASE-DEMO-001",
            user_id=demo_user.user_id,
            bank_name="State Bank of India",
            masked_account_number="XXXX-XXXX-1001",
            freeze_date=datetime.utcnow() - timedelta(days=5),
            restriction_type="DEBIT_FREEZE",
            freeze_reason="P2P Disputed Transaction Flagged by Cyber Cell [DEMO DATA]",
            status="CASE_ANALYSIS",
            metadata_json='{"tags": ["P2P", "Cyber Cell", "UPI Dispute"], "demo_label": "[DEMO DATA]"}'
        )
        db.add(c1)
        db.flush()

        t1 = Transaction(
            transaction_id="TXN-DEMO-001",
            case_id=c1.case_id,
            amount=18500.0,
            transaction_date=datetime.utcnow() - timedelta(days=7),
            dispute_status="DISPUTED",
            source="BANK_ADAPTER",
            description="P2P Crypto/UPI Transfer disputed by counterparty [DEMO DATA]"
        )
        a1 = Authority(
            case_id=c1.case_id,
            authority_name="Cyber Crime Police Station",
            jurisdiction="Cyberabad / Hyderabad, Telangana",
            reference_number="LEA-DEMO-001",
            officer_name="Inspector K. Sharma (Cyber Cell)",
            contact_information="cybercrime-hyd-demo@police.gov.in",
            source="UPLOADED_NOTICE",
            confidence="HIGH"
        )
        d1 = Document(
            case_id=c1.case_id,
            filename="demo_notice_p2p_dispute.txt",
            document_type="POLICE_NOTICE",
            extracted_text=read_sample("demo_notice_p2p_dispute.txt")
        )
        task1 = Task(
            case_id=c1.case_id,
            title="Submit P2P Trade Proofs",
            description="Collate exchange order ID, chat receipt, and counterparty KYC confirmation to IO.",
            status="PENDING"
        )
        db.add_all([t1, a1, d1, task1])

        # --- CASE 2: Cybercrime 1930 Portal Notice ---
        c2 = Case(
            case_id="CASE-DEMO-002",
            user_id=demo_user.user_id,
            bank_name="HDFC Bank",
            masked_account_number="XXXX-XXXX-2002",
            freeze_date=datetime.utcnow() - timedelta(days=12),
            restriction_type="LIEN_AMOUNT",
            freeze_reason="1930 National Cyber Crime Reporting Portal Phishing Lien [DEMO DATA]",
            status="ACTION_REQUIRED",
            metadata_json='{"tags": ["1930", "NCRRP", "Phishing Flow"], "demo_label": "[DEMO DATA]"}'
        )
        db.add(c2)
        db.flush()

        t2 = Transaction(
            transaction_id="TXN-DEMO-002",
            case_id=c2.case_id,
            amount=54200.0,
            transaction_date=datetime.utcnow() - timedelta(days=14),
            dispute_status="DISPUTED",
            source="NOTICE_DOC",
            description="Reported phishing layered remittance [DEMO DATA]"
        )
        a2 = Authority(
            case_id=c2.case_id,
            authority_name="National Cyber Crime Reporting Portal (NCRRP)",
            jurisdiction="New Delhi / NCR Central",
            reference_number="NCRRP-2025-88412",
            officer_name="Nodal Desk Cyber Division",
            contact_information="nodal-cyber-demo@gov.in / Helpline 1930",
            source="UPLOADED_NOTICE",
            confidence="HIGH"
        )
        d2 = Document(
            case_id=c2.case_id,
            filename="demo_notice_cybercrime_1930.txt",
            document_type="CYBER_NOTICE",
            extracted_text=read_sample("demo_notice_cybercrime_1930.txt")
        )
        comm2 = Communication(
            case_id=c2.case_id,
            recipient_type="LAW_ENFORCEMENT",
            subject="Factual Submission & Request for Clarification - Ref: NCRRP-2025-88412",
            body="[Draft Generated by AI - Pending Human Review and Approval]",
            status="DRAFT"
        )
        db.add_all([t2, a2, d2, comm2])

        # --- CASE 3: KYC Non-Compliance Freeze ---
        c3 = Case(
            case_id="CASE-DEMO-003",
            user_id=demo_user.user_id,
            bank_name="ICICI Bank",
            masked_account_number="XXXX-XXXX-3003",
            freeze_date=datetime.utcnow() - timedelta(days=25),
            restriction_type="TOTAL_FREEZE",
            freeze_reason="Periodic Re-KYC Statutory Non-Compliance Hold [DEMO DATA]",
            status="WAITING_FOR_INFORMATION",
            metadata_json='{"tags": ["KYC", "Regulatory", "Branch Operations"], "demo_label": "[DEMO DATA]"}'
        )
        db.add(c3)
        db.flush()

        t3 = Transaction(
            transaction_id="TXN-DEMO-003",
            case_id=c3.case_id,
            amount=0.0,
            transaction_date=datetime.utcnow() - timedelta(days=30),
            dispute_status="CLEARED",
            source="USER_STATEMENT",
            description="Operational maintenance hold; no disputed external transaction [DEMO DATA]"
        )
        a3 = Authority(
            case_id=c3.case_id,
            authority_name="Bank Internal Risk & Compliance",
            jurisdiction="Mumbai Central",
            reference_number="BNK-KYC-99012",
            officer_name="Branch Operations Manager",
            contact_information="kyc-compliance-demo@icici-mock.com",
            source="BANK_NOTICE",
            confidence="HIGH"
        )
        d3 = Document(
            case_id=c3.case_id,
            filename="demo_notice_kyc_freeze.txt",
            document_type="KYC_NOTICE",
            extracted_text=read_sample("demo_notice_kyc_freeze.txt")
        )
        db.add_all([t3, a3, d3])

        # --- CASE 4: Court Attachment Order (Sec 102 CrPC) ---
        c4 = Case(
            case_id="CASE-DEMO-004",
            user_id=demo_user.user_id,
            bank_name="Axis Bank",
            masked_account_number="XXXX-XXXX-4004",
            freeze_date=datetime.utcnow() - timedelta(days=40),
            restriction_type="TOTAL_FREEZE",
            freeze_reason="Magistrate Court Attachment Order under Sec 102 CrPC [DEMO DATA]",
            status="ESCALATION_REQUIRED",
            metadata_json='{"tags": ["Court Order", "Sec 102 CrPC", "Magistrate"], "demo_label": "[DEMO DATA]"}'
        )
        db.add(c4)
        db.flush()

        t4 = Transaction(
            transaction_id="TXN-DEMO-004",
            case_id=c4.case_id,
            amount=250000.0,
            transaction_date=datetime.utcnow() - timedelta(days=45),
            dispute_status="FLAGGED",
            source="COURT_ORDER",
            description="Judicial attachment in commercial dispute CC-NO-4402/2025 [DEMO DATA]"
        )
        a4 = Authority(
            case_id=c4.case_id,
            authority_name="Hon'ble Chief Metropolitan Magistrate Court",
            jurisdiction="Bengaluru Rural District",
            reference_number="SEC91-COURT-2025-04",
            officer_name="Registrar / Judicial Bench-3",
            contact_information="cmm-bengaluru-demo@ecourts.gov.in",
            source="COURT_ATTACHMENT",
            confidence="HIGH"
        )
        d4 = Document(
            case_id=c4.case_id,
            filename="demo_notice_court_attachment.txt",
            document_type="COURT_ORDER",
            extracted_text=read_sample("demo_notice_court_attachment.txt")
        )
        esc4 = Escalation(
            case_id=c4.case_id,
            level="LEVEL_3",
            reason="Court attachment requires advocate appearance and bond under Sec 451/457 CrPC.",
            channel="Hon'ble Magistrate Court Bengaluru Bench-3 [DEMO]",
            status="PENDING"
        )
        db.add_all([t4, a4, d4, esc4])

        # --- CASE 5: Unknown Reason / Internal Mismatch ---
        c5 = Case(
            case_id="CASE-DEMO-005",
            user_id=demo_user.user_id,
            bank_name="Punjab National Bank",
            masked_account_number="XXXX-XXXX-5005",
            freeze_date=datetime.utcnow() - timedelta(days=2),
            restriction_type="DEBIT_FREEZE",
            freeze_reason="Internal Bank Surveillance Hold - External Reason Unspecified [DEMO DATA]",
            status="BANK_VERIFICATION",
            metadata_json='{"tags": ["Internal Hold", "Mismatch", "Investigation Needed"], "demo_label": "[DEMO DATA]"}'
        )
        db.add(c5)
        db.flush()

        t5 = Transaction(
            transaction_id="TXN-DEMO-005",
            case_id=c5.case_id,
            amount=78000.0,
            transaction_date=datetime.utcnow() - timedelta(days=4),
            dispute_status="DISPUTED",
            source="USER_STATEMENT",
            description="Suspect mismatch between internal AML flag and customer statement [DEMO DATA]"
        )
        a5 = Authority(
            case_id=c5.case_id,
            authority_name="AML Suspicious Activity Unit",
            jurisdiction="Kolkata Regional Directorate",
            reference_number="AML-ALERT-771",
            officer_name="Senior AML Investigator",
            contact_information="aml-desk-demo@pnb-mock.in",
            source="BANK_ADAPTER",
            confidence="LOW"
        )
        d5 = Document(
            case_id=c5.case_id,
            filename="demo_notice_unknown_freeze.txt",
            document_type="BANK_NOTICE",
            extracted_text=read_sample("demo_notice_unknown_freeze.txt")
        )
        db.add_all([t5, a5, d5])

        # Seed initial audit logs
        cases = [c1, c2, c3, c4, c5]
        for c in cases:
            db.add(AuditLog(
                case_id=c.case_id,
                actor="SYSTEM",
                action="INITIALIZE_SYNTHETIC_CASE",
                timestamp=datetime.utcnow() - timedelta(days=2),
                result="SUCCESS",
                details=f"Synthetic demonstration record initialized for {c.case_id} ({c.bank_name})."
            ))

        db.commit()

if __name__ == "__main__":
    seed_database()
    print("Synthetic demo database seeded successfully.")
