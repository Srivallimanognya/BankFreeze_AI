"""
Audit Logging Module for BankFreeze AI
Ensures immutable chronological audit records for every user and AI action.
"""

import json
from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy.orm import Session
from database.models import AuditLog

def log_audit(
    db: Session,
    action: str,
    actor: str = "SYSTEM",
    case_id: Optional[str] = None,
    result: str = "SUCCESS",
    details: Optional[Any] = None
) -> AuditLog:
    """
    Record an immutable audit log entry in the database.
    """
    details_str = None
    if details is not None:
        if isinstance(details, (dict, list)):
            try:
                details_str = json.dumps(details, default=str)
            except Exception:
                details_str = str(details)
        else:
            details_str = str(details)

    log_entry = AuditLog(
        case_id=case_id,
        actor=actor,
        action=action,
        timestamp=datetime.now(timezone.utc),
        result=result,
        details=details_str
    )
    db.add(log_entry)
    db.flush()
    return log_entry
