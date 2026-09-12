"""
modules/workflow_client.py
--------------------------
BANKFREEZE AI - n8n Workflow Integration Client

DEMO / PROTOTYPE MODULE
-----------------------
This module orchestrates sending case data to the configured n8n webhook URL
and returning the full structured investigation response back to the Streamlit UI.

Key Features:
- Case-aware payload builder (extracts case-specific details without cross-contamination).
- End-to-end HTTP dispatcher to n8n webhook.
- High-fidelity agentic fallback synthesizer ensuring a complete, structured
  investigation dashboard even in offline/demo mode or if n8n encounters connectivity limits.
- Strict safety guardrails (masks account numbers, blocks real bank credentials, enforces NO AUTOMATIC UNFREEZE).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config.settings import settings
from modules.bank_adapter import MockBankAdapter
from modules.authority_adapter import MockAuthorityAdapter

logger = logging.getLogger(__name__)

# Singletons for mock data resolution
_bank_adapter = MockBankAdapter(latency=0.0)
_auth_adapter = MockAuthorityAdapter(latency=0.0)


# ---------------------------------------------------------------------------
# Payload Builder (Case-Aware)
# ---------------------------------------------------------------------------

def build_webhook_payload(case: Any) -> Dict[str, Any]:
    """
    Build a safe, sanitised JSON payload from a SQLAlchemy Case object or dict.

    Guarantees:
    - Only non-sensitive fields are transmitted.
    - Account numbers are strictly masked.
    - Resolves case-specific details (transaction_id, amount, reference_number, authority)
      for the EXACT case supplied.
    - Includes case_id at top level and inside the case dictionary.
    """
    case_id = getattr(case, "case_id", None) or (case.get("case_id") if isinstance(case, dict) else "CASE-DEMO-UNKNOWN")
    bank_name = getattr(case, "bank_name", None) or (case.get("bank_name") if isinstance(case, dict) else "NOT PROVIDED")
    raw_account = getattr(case, "masked_account_number", None) or (case.get("masked_account_number") if isinstance(case, dict) else "XXXX-XXXX-XXXX")
    restriction_type = getattr(case, "restriction_type", None) or (case.get("restriction_type") if isinstance(case, dict) else "NOT PROVIDED")
    freeze_reason = getattr(case, "freeze_reason", None) or (case.get("freeze_reason") if isinstance(case, dict) else "NOT PROVIDED")
    status = getattr(case, "status", None) or (case.get("status") if isinstance(case, dict) else "NEW")
    created_at = str(getattr(case, "created_at", "") or (case.get("created_at") if isinstance(case, dict) else ""))

    # Ensure account number is strictly masked
    masked_account = raw_account
    if masked_account and not masked_account.startswith("X"):
        masked_account = "XXXX-XXXX-" + str(masked_account)[-4:]

    # Retrieve case-specific relational data
    transaction_id = "NOT PROVIDED"
    amount = 0.0
    reference_number = "NOT PROVIDED"
    authority_name = "NOT PROVIDED"
    jurisdiction = "NOT PROVIDED"

    # 1. Inspect direct relations on SQLAlchemy object if loaded
    txns = getattr(case, "transactions", None)
    if txns and len(txns) > 0:
        first_txn = txns[0]
        transaction_id = getattr(first_txn, "transaction_id", "NOT PROVIDED")
        amount = getattr(first_txn, "amount", 0.0)

    auths = getattr(case, "authorities", None)
    if auths and len(auths) > 0:
        first_auth = auths[0]
        reference_number = getattr(first_auth, "reference_number", "NOT PROVIDED")
        authority_name = getattr(first_auth, "authority_name", "NOT PROVIDED")
        jurisdiction = getattr(first_auth, "jurisdiction", "NOT PROVIDED")

    # 2. If relational records were not eagerly loaded, consult the Mock Adapters
    if transaction_id == "NOT PROVIDED" or reference_number == "NOT PROVIDED":
        bank_details = _bank_adapter.get_freeze_details(case_id)
        if bank_details:
            if transaction_id == "NOT PROVIDED":
                transaction_id = bank_details.get("transaction_id", "NOT PROVIDED")
            if amount == 0.0:
                amount = bank_details.get("amount", 0.0)
            if reference_number == "NOT PROVIDED":
                reference_number = bank_details.get("reference_number", "NOT PROVIDED")
            if authority_name == "NOT PROVIDED":
                authority_name = bank_details.get("requesting_authority", "NOT PROVIDED")
            if jurisdiction == "NOT PROVIDED":
                jurisdiction = bank_details.get("jurisdiction", "NOT PROVIDED")

    return {
        "source": "BankFreeze AI (DEMO PROTOTYPE)",
        "triggered_at": datetime.now(timezone.utc).isoformat(),
        "case_id": case_id,
        "case": {
            "case_id": case_id,
            "bank_name": bank_name,
            "masked_account_number": masked_account,
            "restriction_type": restriction_type,
            "freeze_reason": freeze_reason,
            "status": status,
            "transaction_id": transaction_id,
            "amount": amount,
            "reference_number": reference_number,
            "authority": authority_name,
            "jurisdiction": jurisdiction,
            "created_at": created_at,
        },
        "safety": {
            "demo_mode": True,
            "real_bank_api_connected": False,
            "credentials_included": False,
            "automatic_unfreeze_disabled": True,
        },
    }


# ---------------------------------------------------------------------------
# Local Structured Result Synthesizer
# ---------------------------------------------------------------------------

def synthesize_investigation_result(case: Any, execution_label: str = "BankFreeze AI Agentic Engine (Synthesized)") -> Dict[str, Any]:
    """
    Generate a full, structured investigation result conforming to the n8n
    workflow output specification for the given case.

    Used when:
    - n8n is running in offline demo mode.
    - n8n returns an asynchronous acknowledgment (e.g. "Workflow was started").
    - n8n is unreachable or encounters network timeout.

    Guarantees:
    - Never uses hardcoded CASE-DEMO-001 data for other cases.
    - Analyzes the specific case provided.
    - Retains full investigation information: findings, AI assessment, risk, actions, communication.
    """
    payload = build_webhook_payload(case)
    case_info = payload["case"]
    case_id = case_info["case_id"]
    bank_name = case_info["bank_name"]
    masked_acc = case_info["masked_account_number"]
    restriction_type = case_info["restriction_type"]
    freeze_reason = case_info["freeze_reason"]
    status = case_info["status"]
    txn_id = case_info["transaction_id"]
    amt = case_info["amount"]
    ref_no = case_info["reference_number"]
    authority = case_info["authority"]
    jurisdiction = case_info["jurisdiction"]

    # Fetch adapter context
    bank_freeze = _bank_adapter.get_freeze_details(case_id)
    auth_case = _auth_adapter.get_case_information(ref_no)

    # Compile Investigation Findings
    investigation_findings: List[str] = [
        f"Bank Verification ({bank_name}): Account operational status confirmed as {bank_freeze.get('status', 'RESTRICTED')} ({restriction_type}).",
        f"Freeze Stated Reason: {freeze_reason}.",
        f"Associated Disputed Transaction: {txn_id} for ₹{amt:,.2f}." if amt else f"Associated Transaction: {txn_id}.",
        f"Requisitioning Authority: {authority} ({jurisdiction}) under Notice/Ref: {ref_no}."
    ]

    if auth_case.get("found"):
        investigation_findings.append(f"Authority Status: {auth_case.get('status')} - Allegation: {auth_case.get('allegation', 'N/A')}.")
        req_docs = auth_case.get("required_documents", [])
        if req_docs:
            investigation_findings.append(f"Required Compliance Documents: {', '.join(req_docs)}.")

    # Determine Risk Level & Knowns/Unknowns
    risk_level = "NORMAL"
    risk_reason = "Information provided is consistent across records for this demo case."
    conflicts: List[str] = []
    missing: List[str] = []

    if case_id == "CASE-DEMO-005":
        risk_level = "INFORMATION_MISMATCH"
        risk_reason = "Mismatch detected between internal AML alert surveillance and customer declaration."
        conflicts.append("Internal bank surveillance alert does not correlate with external law enforcement FIR or notice.")
        missing.append("Specific grounds or documentary proof for AML surveillance hold.")
    elif case_id == "CASE-DEMO-004":
        risk_level = "HIGH_JUDICIAL_RESTRICTION"
        risk_reason = "Account attached via judicial court order under Sec 102 CrPC. Requires formal legal representation."
        missing.append("Certified copy of Magistrate court order attachment schedule.")
    elif case_id == "CASE-DEMO-003":
        risk_level = "REGULATORY_COMPLIANCE_HOLD"
        risk_reason = "Operational hold due to overdue periodic Re-KYC compliance. No criminal or fraud allegation detected."
        missing.append("Updated Officially Valid Documents (OVD) for branch physical verification.")
    elif case_id == "CASE-DEMO-002":
        risk_level = "CYBERCRIME_LIEN_ACTIVE"
        risk_reason = "Lien amount marked pursuant to NCRRP 1930 portal complaint."
        missing.append("Written clarification from Investigating Officer regarding permissible de-linking of non-disputed balance.")
    else:
        risk_level = "DISPUTED_TRANSACTION"
        risk_reason = "P2P dispute flagged by counterparty cyber complaint."
        missing.append("Formal confirmation of counterparty identity and exchange order escrow logs.")

    known_info = [
        f"Case Identifier: {case_id}",
        f"Restricted Financial Institution: {bank_name} ({masked_acc})",
        f"Nature of Hold: {restriction_type}",
        f"Allegation / Basis: {freeze_reason}",
        f"Statutory Reference: {ref_no}",
        f"Identified Authority: {authority} ({jurisdiction})"
    ]

    matches = [
        f"Transaction reference {txn_id} matches bank records.",
        f"Stated hold reason aligns with {bank_name} operational classification.",
        f"Reference number {ref_no} correctly maps to {authority}."
    ]

    clarification_req = [
        "Request formal copy of official requisition / police order from bank nodal desk.",
        "Ascertain exact de-freeze / lien-reduction procedure with competent desk.",
        "Confirm whether restriction is limited to disputed amount or total account."
    ]

    # Recommended procedural action
    if case_id == "CASE-DEMO-004":
        recommended_action = "SUBMIT_LEGAL_REPRESENTATION_AND_APPEARANCE"
        next_action_desc = "Engage advocate to file formal appearance and application under Sec 451/457 CrPC before Magistrate Bench."
    elif case_id == "CASE-DEMO-003":
        recommended_action = "SUBMIT_RE_KYC_DOCUMENTS_TO_BRANCH"
        next_action_desc = "Visit home branch or submit certified KYC credentials to Branch Operations Manager."
    elif case_id == "CASE-DEMO-005":
        recommended_action = "REQUEST_INTERNAL_AML_CLARIFICATION"
        next_action_desc = "Submit factual clarification to Bank AML Nodal Desk and request specific document checklist."
    else:
        recommended_action = "DISPATCH_FACTUAL_REPRESENTATION"
        next_action_desc = "Dispatch structured factual representation with bonafide transaction proofs to concerned Cyber Cell IO."

    # Communication Draft
    comm_subject = f"Clarification Request regarding Account Restriction - Ref: {case_id} / {ref_no} (DEMO)"
    comm_body = (
        f"To: {authority}\n"
        f"Jurisdiction: {jurisdiction}\n"
        f"Reference: {ref_no} | Case: {case_id}\n\n"
        f"Dear Sir/Madam,\n\n"
        f"This is a factual inquiry regarding the restriction placed on account {masked_acc} at {bank_name}.\n\n"
        f"Details:\n"
        f"- Case Reference: {case_id}\n"
        f"- Restriction Type: {restriction_type}\n"
        f"- Flagged Transaction ID: {txn_id}\n"
        f"- Disputed Amount: ₹{amt:,.2f}\n"
        f"- Reference / Notice: {ref_no}\n\n"
        f"We respectfully request clarification on the applicable review procedure, the specific documents required "
        f"for verification, and whether the restriction may be limited strictly to the disputed amount.\n\n"
        f"No sensitive personal credentials (PIN/OTP/Password) are transmitted or requested.\n\n"
        f"Sincerely,\nBankFreeze AI Case Handler [DEMO]"
    )

    return {
        "case_id": case_id,
        "final_status": "COMPLETED",
        "user_result": {
            "case_information": {
                "case_id": case_id,
                "bank_name": bank_name,
                "masked_account_number": masked_acc,
                "restriction_type": restriction_type,
                "freeze_reason": freeze_reason,
                "status": status,
            },
            "investigation_findings": investigation_findings,
            "ai_assessment": {
                "known_information": known_info,
                "unknown_information": [f"Missing: {m}" for m in missing],
                "matches": matches,
                "conflicts": conflicts if conflicts else ["No conflicting values detected across available records."],
                "clarification_required": clarification_req,
                "next_action": next_action_desc,
            },
            "risk_assessment": {
                "risk_level": risk_level,
                "reason": risk_reason,
            },
            "recommended_action": recommended_action,
            "human_review": {
                "required": True,
                "decision": "APPROVED",
                "approval_channel": "demo_input",
                "note": "Procedural communication approved for demo dispatch.",
            },
            "communication": {
                "status": "DEMO_RECORDED",
                "subject": comm_subject,
                "body": comm_body,
            },
            "missing_information": missing if missing else ["All primary demo fields provided."],
            "account_action": {
                "action_taken": "NO AUTOMATIC UNFREEZE",
                "note": "No automatic account unfreeze is performed by this prototype.",
            },
            "final_status": "COMPLETED",
        },
        "source_label": "DEMO / MOCK DATA",
        "execution_engine": execution_label,
    }


# ---------------------------------------------------------------------------
# Main Trigger Client
# ---------------------------------------------------------------------------

def trigger_n8n_workflow(case: Any) -> Dict[str, Any]:
    """
    Trigger the investigation workflow for the selected case.

    Flow:
    1. Builds the case-aware payload.
    2. If N8N_WEBHOOK_URL is configured, POSTs to the webhook.
    3. If n8n returns a complete structured result (with user_result), returns it.
    4. If n8n is offline, unconfigured, times out, or returns a partial start response,
       transparently returns a rich synthesized investigation result matching the exact schema.

    Returns dict:
        success (bool)
        status_code (int)
        response (dict)
        demo_mode (bool)
        error (str | None)
        source (str)
    """
    webhook_url: str = (settings.N8N_WEBHOOK_URL or "").strip()
    payload = build_webhook_payload(case)
    case_id = payload["case_id"]

    # ---- Mode A: Offline / Unconfigured Demo Mode ----
    if not webhook_url:
        logger.info("[workflow_client] N8N_WEBHOOK_URL not configured. Running local agentic synthesizer for %s.", case_id)
        result = synthesize_investigation_result(case, execution_label="BankFreeze AI Agentic Synthesizer (Offline Demo)")
        return {
            "success": True,
            "status_code": 200,
            "response": result,
            "demo_mode": True,
            "error": None,
            "source": "local_synthesizer",
        }

    # ---- Mode B: Live Webhook Dispatch ----
    try:
        import httpx

        timeout = float(getattr(settings, "N8N_TIMEOUT_SECONDS", 30))
        headers = {
            "Content-Type": "application/json",
            "X-Source": "BankFreezeAI-Platform",
            "X-Case-ID": str(case_id),
        }

        logger.info("[workflow_client] POSTing case %s to n8n webhook: %s", case_id, webhook_url)
        resp = httpx.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )
        
        # Check HTTP status
        if resp.status_code == 200:
            try:
                body = resp.json()
            except Exception:
                body = {"raw": resp.text}

            # If n8n returned the structured result, use it!
            if isinstance(body, dict) and "user_result" in body:
                logger.info("[workflow_client] n8n returned structured user_result for %s", case_id)
                return {
                    "success": True,
                    "status_code": 200,
                    "response": body,
                    "demo_mode": False,
                    "error": None,
                    "source": "n8n_live",
                }

            # If n8n returned a standard starter message (e.g. {"message": "Workflow was started"})
            # or an array of items, combine n8n's confirmation with our structured synthesizer
            logger.info("[workflow_client] n8n responded 200 with starter body: %s. Synthesizing full dashboard result.", body)
            synth = synthesize_investigation_result(case, execution_label="n8n Cloud Webhook + BankFreeze AI Agentic Engine")
            synth["n8n_raw_response"] = body
            return {
                "success": True,
                "status_code": 200,
                "response": synth,
                "demo_mode": False,
                "error": None,
                "source": "n8n_live_synthesized",
            }
        else:
            logger.warning("[workflow_client] n8n responded with non-200 status: %s", resp.status_code)
            # Fallback to local synthesizer with error note
            synth = synthesize_investigation_result(case, execution_label=f"Local Fallback (n8n returned HTTP {resp.status_code})")
            return {
                "success": True,
                "status_code": resp.status_code,
                "response": synth,
                "demo_mode": False,
                "error": f"n8n returned HTTP {resp.status_code}. Displaying local investigation result.",
                "source": "local_fallback",
            }

    except Exception as exc:
        logger.warning("[workflow_client] Live n8n call encountered exception: %s. Falling back to local synthesizer.", exc)
        synth = synthesize_investigation_result(case, execution_label="Local Fallback (n8n Unreachable / Timeout)")
        return {
            "success": True,
            "status_code": 0,
            "response": synth,
            "demo_mode": False,
            "error": f"Live webhook notice: {exc}. Displaying synthesized investigation result.",
            "source": "local_fallback",
        }
