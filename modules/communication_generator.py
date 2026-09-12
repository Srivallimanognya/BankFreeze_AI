"""
Communication Generator Module for BankFreeze AI
Generates professional, factual, and compliant draft communications for:
1. Bank Clarification Request
2. Authority Clarification Request
3. Follow-up Communication
4. Escalation Request

Safety & Tone Guardrails:
- Strictly factual
- No accusations, threats, or aggressive language
- No impersonation; clearly drafted on behalf of/by the account holder
- No fabricated legal citations or imaginary case references
"""

from typing import Dict, Any, Optional
from datetime import datetime

class CommunicationGenerator:
    """
    Constructs formal written representations based strictly on verified case facts.
    """

    def generate_bank_clarification(self, case_info: Dict[str, Any]) -> Dict[str, str]:
        bank = case_info.get("bank_name", "[Bank Name]")
        masked_acc = case_info.get("masked_account_number", "XXXX-XXXX-XXXX")
        case_id = case_info.get("case_id", "CASE-REF")
        txn_id = case_info.get("transaction_id", "NOT PROVIDED")
        amt = case_info.get("amount", "NOT PROVIDED")
        ref_no = case_info.get("reference_number", "NOT PROVIDED")
        auth = case_info.get("authority", "NOT PROVIDED")
        freeze_date = case_info.get("freeze_date", datetime.now().strftime("%Y-%m-%d"))

        subject = f"Urgent: Request for Clarification and Specifics Regarding Account Restriction - A/C {masked_acc}"

        body = f"""To,
The Branch Manager / Nodal Grievance Officer,
{bank}

Subject: Request for Written Clarification on Restriction of Account {masked_acc}
Internal Reference ID: {case_id}

Dear Sir / Madam,

I am writing with respect to my savings/current account ending with {masked_acc} maintained at your branch, which has been placed under restriction/freeze on or around {freeze_date}.

According to available notices/records:
- Stated Nature of Restriction: {case_info.get('restriction_type', 'Operational Hold')}
- Flagged Transaction Reference: {txn_id}
- Involved Disputed Amount: ₹{amt if amt != 'NOT PROVIDED' else 'Not Specified'}
- Stated Requesting Authority: {auth}
- Statutory / Police Reference No: {ref_no}

To enable me to cooperate fully and provide appropriate factual clarifications, I respectfully request the following specific particulars:
1. The exact written notice, requisition copy, or statutory order number received by the bank.
2. The specific law enforcement agency, cyber cell, or court bench from which the directive originated, including the nodal officer's official contact information.
3. Confirmation whether the hold is confined strictly to the disputed lien amount (₹{amt if amt != 'NOT PROVIDED' else 'lien amount'}) or represents a blanket debit freeze, in line with applicable regulatory guidelines.
4. The prescribed bank procedure and documentation required to resolve this restriction.

I remain committed to full transparency and cooperation with your compliance team and the concerned authorities.

Yours sincerely,
Account Holder / Authorized Representative
Account No: {masked_acc}
Date: {datetime.now().strftime("%d %B %Y")}
"""
        return {"subject": subject.strip(), "body": body.strip(), "recipient_type": "BANK_NODAL_OFFICER"}

    def generate_authority_clarification(self, case_info: Dict[str, Any]) -> Dict[str, str]:
        auth_name = case_info.get("authority", "Cyber Crime Unit / Law Enforcement Desk")
        jurisdiction = case_info.get("jurisdiction", "Concerned Jurisdiction")
        ref_no = case_info.get("reference_number", "NOT PROVIDED")
        comp_no = case_info.get("complaint_number", "NOT PROVIDED")
        officer = case_info.get("officer_name", "The Investigating Officer (IO)")
        bank = case_info.get("bank_name", "[Bank Name]")
        masked_acc = case_info.get("masked_account_number", "XXXX-XXXX-XXXX")
        txn_id = case_info.get("transaction_id", "NOT PROVIDED")
        amt = case_info.get("amount", "NOT PROVIDED")
        txn_date = case_info.get("transaction_date", "NOT PROVIDED")

        subject = f"Representation regarding Account Restriction Notice - Ref: {ref_no} / Ack: {comp_no}"

        body = f"""To,
{officer},
{auth_name},
{jurisdiction}

Subject: Factual Submission & Request for Clarification - Ref: {ref_no} (Comp No: {comp_no})

Respected Officer,

I submit this formal representation regarding the restriction placed on my bank account ({bank}, A/C ending {masked_acc}) pursuant to a requisition from your esteemed office citing Reference No: {ref_no}.

Factual Particulars of Record:
- Account Holder Reference: Account ending in {masked_acc} at {bank}
- Law Enforcement Reference / Ack No: {ref_no}
- Associated Transaction ID: {txn_id}
- Transaction Date: {txn_date}
- Disputed Sum in Question: ₹{amt if amt != 'NOT PROVIDED' else 'Not Specified'}

Submission:
I have been notified by the bank of an ongoing inquiry in relation to the aforementioned reference. I wish to submit on record that I am a bonafide account holder with no intent to participate in or benefit from any unlawful activity. 

I am prepared to submit all supporting proofs, including:
1. Certified bank statement demonstrating legitimate source and destination of funds.
2. Invoices, commercial purchase/sale receipts, or P2P order documentation verifying the bonafides of the entry.
3. Government-issued identity and address credentials for verification.

Request:
1. Kindly provide the brief nature of the complaint and clarify the specific role attributed to the entry in question.
2. If the investigation relates strictly to the disputed amount of ₹{amt if amt != 'NOT PROVIDED' else 'disputed amount'}, I respectfully request that the bank be instructed to limit the hold to a lien on the disputed sum, thereby enabling normal operations for unaffected legitimate funds.
3. Please advise the earliest opportunity or official email address where my complete documentary proofs may be tendered for prompt verification.

Thanking you for your time and fair consideration.

Respectfully submitted,
Account Holder
Contact: [Verified Account Holder Mobile & Email on File]
Date: {datetime.now().strftime("%d %B %Y")}
"""
        return {"subject": subject.strip(), "body": body.strip(), "recipient_type": "LAW_ENFORCEMENT"}

    def generate_followup(self, case_info: Dict[str, Any], initial_comm_date: Optional[str] = None) -> Dict[str, str]:
        bank = case_info.get("bank_name", "[Bank Name]")
        masked_acc = case_info.get("masked_account_number", "XXXX-XXXX-XXXX")
        ref_no = case_info.get("reference_number", "NOT PROVIDED")
        auth = case_info.get("authority", "Concerned Authority")
        days = "7"

        subject = f"Follow-Up: Status Update Request on Pending Clarification - A/C {masked_acc} (Ref: {ref_no})"

        body = f"""To,
The Nodal Officer / Case Officer,
{bank} / {auth}

Subject: Follow-up on Prior Clarification Submission regarding Account Hold - A/C {masked_acc}
Reference: {ref_no}

Dear Sir / Madam,

This is a respectful follow-up to the formal representation submitted on {initial_comm_date or 'earlier this week'} regarding the debit freeze/hold applied to account ending with {masked_acc}.

As over {days} business days have elapsed since the submission, I kindly request an update on:
1. The status of verification of the submitted documentation and transaction explanation.
2. Whether any additional documents, affidavits, or proofs are required from my side.
3. The expected timeline for issuing a de-freezing order or restricting the hold to the specific disputed lien amount.

Your prompt assistance in resolving this matter will prevent undue financial hardship.

With regards,
Account Holder
A/C: {masked_acc}
Date: {datetime.now().strftime("%d %B %Y")}
"""
        return {"subject": subject.strip(), "body": body.strip(), "recipient_type": "FOLLOW_UP_DESK"}

    def generate_escalation_request(self, case_info: Dict[str, Any], escalation_level: str = "LEVEL_2") -> Dict[str, str]:
        bank = case_info.get("bank_name", "[Bank Name]")
        masked_acc = case_info.get("masked_account_number", "XXXX-XXXX-XXXX")
        ref_no = case_info.get("reference_number", "NOT PROVIDED")
        auth = case_info.get("authority", "Concerned Authority")
        amt = case_info.get("amount", "NOT PROVIDED")

        subject = f"Grievance Escalation ({escalation_level}): Lack of Resolution on Account Freeze - A/C {masked_acc}"

        body = f"""To,
The Principal Nodal Officer / Banking Ombudsman / Senior Cyber Grievance Cell,
{bank}

Subject: Formal Escalation Regarding Unresolved Bank Account Freeze ({escalation_level})
Account Reference: Ending in {masked_acc}
Requisition / Notice Reference: {ref_no}

Respected Authority,

I am formally escalating the matter of an indefinite account restriction placed on account {masked_acc} at {bank}, which has remained unresolved despite initial representations and follow-ups.

Summary of Issue:
- The account was restricted citing Requisition Reference: {ref_no} from {auth}.
- Relevant transaction amount under review: ₹{amt if amt != 'NOT PROVIDED' else 'Not Specified'}.
- While I have expressed full willingness to cooperate and have tendered necessary proofs, no formal status report or lien-modification has been executed.
- The total debit freeze across all legitimate funds exceeds the statutory requirement and inflicts severe hardship on daily livelihood and essential obligations.

Relief Requested:
1. Immediate review by the Senior Grievance Committee.
2. Direct the branch to restrict the hold to a lien strictly on the disputed amount (₹{amt}), allowing unrestricted operation of remaining legitimate balances, in accordance with applicable regulatory guidelines and judicial precedents.
3. Provide an official written status within the statutory grievance redressal timeframe.

Yours faithfully,
Account Holder
Date: {datetime.now().strftime("%d %B %Y")}
"""
        return {"subject": subject.strip(), "body": body.strip(), "recipient_type": "GRIEVANCE_DESK"}

communication_generator = CommunicationGenerator()
