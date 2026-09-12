"""
Security and Redaction Module for BankFreeze AI
Implements password hashing (bcrypt), account number masking,
and sensitive credential filtering (guards against storing OTP, PINs, CVVs).
"""

import re
import bcrypt
from typing import Tuple, List
from config.settings import settings

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with salt."""
    if not password:
        raise ValueError("Password cannot be empty")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    if not password or not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def mask_account_number(account_number: str) -> str:
    """
    Mask a bank account number.
    Preserves only the last 4 digits, replacing prior digits with 'XXXX-XXXX-'.
    Example: '123456789012' -> 'XXXX-XXXX-9012'
    """
    if not account_number:
        return "XXXX-XXXX-0000"
    
    # Strip spaces and dashes
    cleaned = re.sub(r"[^\w]", "", str(account_number)).strip()
    if len(cleaned) <= 4:
        return f"XXXX-XXXX-{cleaned}"
    
    last_four = cleaned[-4:]
    return f"XXXX-XXXX-{last_four}"

def detect_prohibited_credentials(text: str) -> Tuple[bool, List[str]]:
    """
    Check if text contains forbidden credentials such as OTP, CVV, ATM PIN, or Netbanking passwords.
    Returns (has_prohibited, list_of_detected_terms).
    """
    if not text:
        return False, []
    
    lower_text = text.lower()
    detected = []
    
    # Check forbidden terms
    for term in settings.FORBIDDEN_CREDENTIAL_TERMS:
        # Match as whole word or phrase
        pattern = r"\b" + re.escape(term) + r"\b"
        if re.search(pattern, lower_text):
            detected.append(term.upper())
            
    # Pattern checks for potential explicit CVV/PIN disclosures
    # e.g., "cvv: 123" or "pin: 1234"
    if re.search(r"\bcvv\s*[:=]?\s*\d{3,4}\b", lower_text):
        if "CVV" not in detected:
            detected.append("CVV")
    if re.search(r"\b(atm\s*pin|upi\s*pin|mpin)\s*[:=]?\s*\d{4,6}\b", lower_text):
        if "PIN" not in detected:
            detected.append("PIN")
    if re.search(r"\botp\s*[:=]?\s*\d{4,8}\b", lower_text):
        if "OTP" not in detected:
            detected.append("OTP")

    return len(detected) > 0, detected

def sanitize_and_redact_text(text: str) -> str:
    """
    Redact any accidental card numbers, CVVs, or OTP numbers from text.
    """
    if not text:
        return ""
    
    redacted = text
    # Redact 16-digit card numbers
    redacted = re.sub(r"\b(?:\d[ -]*?){13,16}\b", "[REDACTED_CARD_NUMBER]", redacted)
    # Redact explicit CVV
    redacted = re.sub(r"(?i)\bcvv\s*[:=]?\s*\d{3,4}\b", "CVV: [REDACTED]", redacted)
    # Redact explicit OTP
    redacted = re.sub(r"(?i)\botp\s*[:=]?\s*\d{4,8}\b", "OTP: [REDACTED]", redacted)
    # Redact PINs
    redacted = re.sub(r"(?i)\b(atm\s*pin|upi\s*pin|mpin)\s*[:=]?\s*\d{4,6}\b", r"\1: [REDACTED]", redacted)
    
    return redacted
