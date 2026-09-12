"""
Unit tests for Security Guardrails, Password Hashing, Masking, and Credential Filtering.
"""

import pytest
from modules.security import (
    hash_password,
    verify_password,
    mask_account_number,
    detect_prohibited_credentials,
    sanitize_and_redact_text
)

def test_bcrypt_hashing_and_verification():
    raw_pass = "ComplianceAdmin@2025!"
    hashed = hash_password(raw_pass)
    
    assert hashed != raw_pass
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_account_masking():
    assert mask_account_number("123456789012") == "XXXX-XXXX-9012"
    assert mask_account_number("50100456789123") == "XXXX-XXXX-9123"
    assert mask_account_number("1234") == "XXXX-XXXX-1234"
    assert mask_account_number("") == "XXXX-XXXX-0000"

def test_prohibited_credential_detection():
    # Detect OTP
    has_otp, terms = detect_prohibited_credentials("Please check my OTP: 449210")
    assert has_otp is True
    assert "OTP" in terms

    # Detect CVV
    has_cvv, terms = detect_prohibited_credentials("Card ending 1234 with cvv 789")
    assert has_cvv is True
    assert "CVV" in terms

    # Detect UPI PIN / ATM PIN
    has_pin, terms = detect_prohibited_credentials("My upi pin is 1234")
    assert has_pin is True
    assert any("PIN" in t for t in terms)

    # Safe text should not trigger detection
    has_clean, terms = detect_prohibited_credentials("Account frozen under cyber crime complaint ref LEA-001")
    assert has_clean is False
    assert len(terms) == 0

def test_sanitization_and_redaction():
    unsafe_text = "Card 4111222233334444 CVV: 123 OTP: 998877"
    redacted = sanitize_and_redact_text(unsafe_text)
    
    assert "4111222233334444" not in redacted
    assert "[REDACTED" in redacted
    assert "CVV: [REDACTED]" in redacted
    assert "OTP: [REDACTED]" in redacted
