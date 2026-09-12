"""
Resolution Agent Module for BankFreeze AI
Provides agentic reasoning over bank-account freeze cases.
Answers:
- What is known?
- What is unknown?
- What information conflicts?
- What should be requested?
- Who should be contacted?
- What documents should be prepared?
- What follow-up is required?
- Whether escalation is appropriate.

Safety Guardrail:
- NEVER claims an account can be unfrozen directly.
- NEVER recommends final resolution when critical information conflicts.
- Always recommends structured factual inquiries and human review.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from database.models import Case, Document, Transaction, Authority, Communication, Task, AuditLog, Escalation
from schemas.case import CaseStatus, ConfidenceLevel, FactType
from modules.bank_adapter import MockBankAdapter
from modules.authority_adapter import MockAuthorityAdapter
from modules.reconciliation import MultiSourceReconciler, reconciler
from modules.communication_generator import communication_generator
from modules.escalation import escalation_engine
from modules.audit import log_audit
from modules.freeze_analyzer import freeze_analyzer

class ResolutionAgent:
    """
    Autonomous reasoning agent equipped with 11 specialized tools to investigate cases.
    """

    def __init__(self, db: Session):
        self.db = db
        self.bank_adapter = MockBankAdapter()
        self.authority_adapter = MockAuthorityAdapter()

    # --- Tool 1: get_case ---
    def get_case(self, case_id: str) -> Optional[Case]:
        return self.db.query(Case).filter(Case.case_id == case_id).first()

    # --- Tool 2: get_bank_information ---
    def get_bank_information(self, case_id: str) -> Dict[str, Any]:
        case = self.get_case(case_id)
        if not case:
            return {}
        status = self.bank_adapter.get_account_status(case.case_id)
        freeze = self.bank_adapter.get_freeze_details(case.case_id)
        return {**status, **freeze}

    # --- Tool 3: get_authority_information ---
    def get_authority_information(self, case_id: str) -> Dict[str, Any]:
        case = self.get_case(case_id)
        if not case:
            return {}
        # Fetch existing authority record from DB or query adapter via reference_number
        auth = self.db.query(Authority).filter(Authority.case_id == case_id).first()
        ref = auth.reference_number if auth else "LEA-DEMO-001"
        return self.authority_adapter.get_case_information(ref)

    # --- Tool 4: get_documents ---
    def get_documents(self, case_id: str) -> List[Document]:
        return self.db.query(Document).filter(Document.case_id == case_id).all()

    # --- Tool 5: compare_sources ---
    def compare_sources(self, case_id: str) -> Dict[str, Any]:
        case = self.get_case(case_id)
        if not case:
            return {"error": "Case not found"}

        user_info = {
            "transaction_id": getattr(case, "transaction_id", None) or "NOT PROVIDED",
            "amount": getattr(case, "disputed_amount", None) or "NOT PROVIDED",
            "freeze_reason": case.freeze_reason,
            "authority": "NOT PROVIDED",
            "reference_number": "NOT PROVIDED"
        }

        # Check latest document
        docs = self.get_documents(case_id)
        doc_result = None
        if docs:
            from modules.document_analyzer import document_analyzer
            doc_result = document_analyzer.analyze_document(docs[0].extracted_text or "", docs[0].filename)

        bank_info = self.get_bank_information(case_id)
        auth_info = self.get_authority_information(case_id)

        result = reconciler.reconcile_case(
            case_id=case_id,
            user_info=user_info,
            document_result=doc_result,
            bank_details=bank_info,
            authority_details=auth_info
        )
        return result.model_dump()

    # --- Tool 6: generate_inquiry ---
    def generate_inquiry(self, case_id: str, target: str = "BANK") -> Communication:
        case = self.get_case(case_id)
        case_dict = self._build_case_context(case_id)
        if target == "BANK":
            draft = communication_generator.generate_bank_clarification(case_dict)
        else:
            draft = communication_generator.generate_authority_clarification(case_dict)

        comm = Communication(
            case_id=case_id,
            recipient_type=draft["recipient_type"],
            subject=draft["subject"],
            body=draft["body"],
            status="DRAFT"
        )
        self.db.add(comm)
        self.db.commit()
        log_audit(self.db, action=f"GENERATE_{target}_INQUIRY_DRAFT", actor="AI_AGENT", case_id=case_id, result="SUCCESS")
        return comm

    # --- Tool 7: generate_followup ---
    def generate_followup(self, case_id: str) -> Communication:
        case_dict = self._build_case_context(case_id)
        draft = communication_generator.generate_followup(case_dict)
        comm = Communication(
            case_id=case_id,
            recipient_type=draft["recipient_type"],
            subject=draft["subject"],
            body=draft["body"],
            status="DRAFT"
        )
        self.db.add(comm)
        self.db.commit()
        log_audit(self.db, action="GENERATE_FOLLOWUP_DRAFT", actor="AI_AGENT", case_id=case_id, result="SUCCESS")
        return comm

    # --- Tool 8: generate_escalation ---
    def generate_escalation(self, case_id: str, level: str = "LEVEL_2") -> Communication:
        case_dict = self._build_case_context(case_id)
        draft = communication_generator.generate_escalation_request(case_dict, level)
        comm = Communication(
            case_id=case_id,
            recipient_type=draft["recipient_type"],
            subject=draft["subject"],
            body=draft["body"],
            status="DRAFT"
        )
        self.db.add(comm)
        self.db.commit()
        log_audit(self.db, action=f"GENERATE_ESCALATION_DRAFT_{level}", actor="AI_AGENT", case_id=case_id, result="SUCCESS")
        return comm

    # --- Tool 9: update_case_status ---
    def update_case_status(self, case_id: str, new_status: CaseStatus) -> Case:
        case = self.get_case(case_id)
        old_status = case.status
        case.status = new_status.value
        self.db.commit()
        log_audit(
            self.db,
            action="UPDATE_CASE_STATUS",
            actor="AI_AGENT",
            case_id=case_id,
            result="SUCCESS",
            details={"old_status": old_status, "new_status": new_status.value}
        )
        return case

    # --- Tool 10: create_task ---
    def create_task(self, case_id: str, title: str, description: str) -> Task:
        task = Task(
            case_id=case_id,
            title=title,
            description=description,
            status="PENDING"
        )
        self.db.add(task)
        self.db.commit()
        log_audit(self.db, action="CREATE_INVESTIGATION_TASK", actor="AI_AGENT", case_id=case_id, result="SUCCESS", details={"title": title})
        return task

    # --- Tool 11: create_audit_log ---
    def create_audit_log(self, case_id: str, action: str, result: str, details: Any) -> AuditLog:
        return log_audit(self.db, action=action, actor="AI_AGENT", case_id=case_id, result=result, details=details)

    # --- High-Level Agentic Reasoning Engine ---
    def reason_and_synthesize(self, case_id: str) -> Dict[str, Any]:
        """
        Executes full reasoning over the case state:
        Evaluates knowns, unknowns, conflicts, requested items, who to contact,
        documents to prepare, follow-ups, and escalation readiness.
        """
        case = self.get_case(case_id)
        if not case:
            return {"error": "Case not found"}

        recon = self.compare_sources(case_id)
        bank_info = self.get_bank_information(case_id)
        auth_info = self.get_authority_information(case_id)
        docs = self.get_documents(case_id)
        txns = self.db.query(Transaction).filter(Transaction.case_id == case_id).all()

        knowns = []
        unknowns = []
        conflicts = recon.get("conflict_summary", [])
        has_critical_conflicts = recon.get("has_critical_conflicts", False)

        # What is known?
        knowns.append(f"Bank Account: {case.bank_name} ({case.masked_account_number})")
        knowns.append(f"Restriction Type: {case.restriction_type}")
        knowns.append(f"Current Lifecycle State: {case.status}")

        if bank_info.get("requesting_authority"):
            knowns.append(f"Requesting Authority: {bank_info.get('requesting_authority')}")
        if bank_info.get("reference_number"):
            knowns.append(f"Statutory / Notice Ref: {bank_info.get('reference_number')}")
        if txns:
            knowns.append(f"Recorded Disputed Amount: ₹{txns[0].amount:,.2f} (Txn ID: {txns[0].transaction_id})")

        # What is unknown?
        for comp in recon.get("comparisons", []):
            if comp["status"] == "MISSING":
                unknowns.append(f"{comp['field_name']}: Not found across submitted records")
        if not docs:
            unknowns.append("Formal freeze notice / requisition copy: Not yet uploaded by user")
        if not auth_info.get("officer_name") or auth_info.get("officer_name") == "NOT PROVIDED":
            unknowns.append("Investigating Officer (IO) direct designation and desk details")

        # Who should be contacted?
        contact_targets = []
        if bank_info.get("bank_name"):
            contact_targets.append({
                "target": f"{case.bank_name} Branch Manager & Nodal Officer",
                "role": "Bank Operations & Lien Verification",
                "purpose": "Request formal copy of police requisition and verify if lien can be restricted to disputed amount"
            })
        if bank_info.get("requesting_authority"):
            contact_targets.append({
                "target": f"{bank_info.get('requesting_authority')} ({bank_info.get('jurisdiction', 'Jurisdiction')})",
                "role": "Law Enforcement / Requisitioning Body",
                "purpose": "Submit factual representation, statement proof, and bonafide transaction justification"
            })

        # What documents should be prepared?
        docs_to_prepare = [
            "Official Bank Statement for preceding 6 months (certified by branch)",
            "Bonafide Proof of Disputed Transaction (Tax Invoice, P2P Order Receipt, or Contract)",
            "Government Photo Identity Proof (Aadhaar / PAN Card)",
            "Written Representation addressed to the Investigating Officer (IO)"
        ]

        # Resolution Recommendation Logic
        recommendations = []
        if has_critical_conflicts:
            recommendations.append(
                "CRITICAL WARNING: Factual discrepancies exist between bank records and notice details. "
                "Do NOT request immediate closure. Step 1 must be a factual clarification request to the bank nodal desk."
            )
        else:
            if not docs:
                recommendations.append("Upload the official freeze notice received from the bank or cyber cell.")
            if case.status in [CaseStatus.NEW.value, CaseStatus.BANK_VERIFICATION.value]:
                recommendations.append("Dispatch formal bank clarification request to obtain copy of requisition.")
            elif case.status in [CaseStatus.AUTHORITY_IDENTIFICATION.value, CaseStatus.AUTHORITY_INQUIRY_REQUIRED.value]:
                recommendations.append("Prepare and tender factual submission to the concerned Cyber Crime Unit.")
            elif case.status == CaseStatus.FOLLOW_UP_REQUIRED.value:
                recommendations.append("Issue respectful status follow-up citing pending 7+ day window.")
            elif case.status == CaseStatus.ESCALATION_REQUIRED.value:
                recommendations.append("Initiate Level 2 Grievance Escalation to Principal Nodal Officer.")

        # Escalation check
        esc_eval = escalation_engine.evaluate_escalation_readiness(
            case_status=case.status,
            initial_comm_date=case.created_at,
            current_escalation_level="LEVEL_1"
        )

        return {
            "case_id": case_id,
            "status": case.status,
            "knowns": knowns,
            "unknowns": unknowns,
            "conflicts": conflicts,
            "has_critical_conflicts": has_critical_conflicts,
            "can_recommend_resolution": not has_critical_conflicts,
            "contact_targets": contact_targets,
            "documents_to_prepare": docs_to_prepare,
            "recommended_actions": recommendations,
            "escalation_readiness": esc_eval,
            "guardrail_notice": (
                "IMPORTANT SAFETY GUARDRAIL: BankFreeze AI never claims an account can be automatically unfrozen. "
                "All recommendations are procedural and require explicit human approval."
            )
        }

    def _build_case_context(self, case_id: str) -> Dict[str, Any]:
        case = self.get_case(case_id)
        bank_info = self.get_bank_information(case_id)
        auth_info = self.get_authority_information(case_id)
        txns = self.db.query(Transaction).filter(Transaction.case_id == case_id).all()

        txn_id = txns[0].transaction_id if txns else bank_info.get("transaction_id", "NOT PROVIDED")
        amt = str(txns[0].amount) if txns else str(bank_info.get("amount", "NOT PROVIDED"))

        return {
            "case_id": case.case_id,
            "bank_name": case.bank_name,
            "masked_account_number": case.masked_account_number,
            "freeze_date": case.freeze_date.strftime("%Y-%m-%d"),
            "restriction_type": case.restriction_type,
            "freeze_reason": case.freeze_reason,
            "transaction_id": txn_id,
            "amount": amt,
            "authority": bank_info.get("requesting_authority") or auth_info.get("authority_name", "Cyber Crime Unit"),
            "jurisdiction": bank_info.get("jurisdiction") or auth_info.get("jurisdiction", "Jurisdiction"),
            "reference_number": bank_info.get("reference_number") or auth_info.get("reference_number", "NOT PROVIDED"),
            "complaint_number": auth_info.get("complaint_number", "NOT PROVIDED"),
            "officer_name": auth_info.get("officer_name", "Investigating Officer (IO)")
        }
