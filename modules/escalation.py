"""
Escalation Module for BankFreeze AI
Implements a 3-tier demonstration escalation workflow:
LEVEL 1: Case-handling channel (Branch operations / investigating desk)
LEVEL 2: Official grievance / nodal channel (Principal Nodal Officer / Ombudsman)
LEVEL 3: Human / Legal counsel recommendation (Magistrate court Sec 451/457 CrPC, High Court writ)
All levels are clearly flagged as DEMONSTRATION WORKFLOW.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from schemas.case import CaseStatus

class EscalationTier:
    def __init__(self, level: str, name: str, description: str, typical_wait_days: int, recommended_channel: str):
        self.level = level
        self.name = name
        self.description = description
        self.typical_wait_days = typical_wait_days
        self.recommended_channel = recommended_channel

class EscalationEngine:
    """
    Tracks and recommends escalation progression based on response windows and case state.
    """

    TIERS = {
        "LEVEL_1": EscalationTier(
            level="LEVEL_1",
            name="Primary Case-Handling Channel",
            description="Initial factual clarification submitted to home branch manager and primary Investigating Officer (IO).",
            typical_wait_days=7,
            recommended_channel="Branch Operations / Assigned Police Station Desk [DEMO]"
        ),
        "LEVEL_2": EscalationTier(
            level="LEVEL_2",
            name="Official Grievance / Nodal Escalation",
            description="Escalation to Bank Principal Nodal Officer, Cyber Crime Cell Supervisory In-charge, or RBI Banking Ombudsman.",
            typical_wait_days=14,
            recommended_channel="Bank Principal Nodal Officer / Cyber Cell ACP/DCP [DEMO]"
        ),
        "LEVEL_3": EscalationTier(
            level="LEVEL_3",
            name="Human / Legal Counsel Recommendation",
            description="Formal judicial application for defreezing or conversion to lien before the jurisdictional Magistrate or High Court.",
            typical_wait_days=30,
            recommended_channel="Advocate Representation / Hon'ble Magistrate Court under Sec 451/457 CrPC [DEMO]"
        ),
    }

    def evaluate_escalation_readiness(
        self,
        case_status: str,
        initial_comm_date: Optional[datetime] = None,
        current_escalation_level: str = "LEVEL_1",
        has_response: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate if a case is ripe for escalation to the next tier.
        """
        if initial_comm_date and initial_comm_date.tzinfo is not None:
            from datetime import timezone
            now = datetime.now(timezone.utc)
        else:
            now = datetime.now()
        days_elapsed = (now - initial_comm_date).days if initial_comm_date else 0
        
        tier_info = self.TIERS.get(current_escalation_level, self.TIERS["LEVEL_1"])
        
        should_escalate = False
        next_level = None
        recommendation = ""

        if not has_response:
            if current_escalation_level == "LEVEL_1" and days_elapsed >= tier_info.typical_wait_days:
                should_escalate = True
                next_level = "LEVEL_2"
                recommendation = (
                    f"No response received after {days_elapsed} days (threshold: {tier_info.typical_wait_days} days). "
                    "Recommend initiating LEVEL 2 Grievance Escalation to the Principal Nodal Officer."
                )
            elif current_escalation_level == "LEVEL_2" and days_elapsed >= tier_info.typical_wait_days:
                should_escalate = True
                next_level = "LEVEL_3"
                recommendation = (
                    f"No resolution obtained from nodal desk after {days_elapsed} days. "
                    "Recommend transitioning to LEVEL 3: Engage independent legal counsel for court representation."
                )
            else:
                remaining = max(0, tier_info.typical_wait_days - days_elapsed)
                recommendation = f"Awaiting response at {tier_info.name}. {remaining} days remaining before next tier escalation."
        else:
            recommendation = "Active response received from respondent. Review findings prior to further escalation."

        return {
            "current_level": current_escalation_level,
            "current_tier_name": tier_info.name,
            "days_elapsed": days_elapsed,
            "threshold_days": tier_info.typical_wait_days,
            "should_escalate": should_escalate,
            "next_level": next_level,
            "recommendation": recommendation,
            "badge": "[DEMO ESCALATION WORKFLOW]"
        }

escalation_engine = EscalationEngine()
