import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables if python-dotenv is present
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "BankFreeze AI")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "demo-secret-key-bankfreeze-2025")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'bankfreeze.db'}")
    
    # LLM Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    
    # Mock Settings
    MOCK_BANK_LATENCY: float = float(os.getenv("MOCK_BANK_LATENCY_SECONDS", "0.1"))
    MOCK_AUTHORITY_LATENCY: float = float(os.getenv("MOCK_AUTHORITY_LATENCY_SECONDS", "0.1"))
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "True").lower() in ("true", "1", "yes")
    
    # n8n Workflow Integration (leave blank to run in offline/demo mode)
    # Reads from environment variable, with fallback to Streamlit Cloud secrets
    _raw_webhook: str = os.getenv("N8N_WEBHOOK_URL", "")
    if not _raw_webhook:
        try:
            import streamlit as st
            _raw_webhook = str(st.secrets.get("N8N_WEBHOOK_URL", ""))
        except Exception:
            _raw_webhook = ""
    N8N_WEBHOOK_URL: str = _raw_webhook
    N8N_TIMEOUT_SECONDS: int = int(os.getenv("N8N_TIMEOUT_SECONDS", "30"))

    
    # Security
    MASK_ACCOUNT_NUMBERS: bool = os.getenv("MASK_ACCOUNT_NUMBERS", "True").lower() in ("true", "1", "yes")
    ENFORCE_STRICT_SAFEGUARDS: bool = os.getenv("ENFORCE_STRICT_SAFEGUARDS", "True").lower() in ("true", "1", "yes")
    
    # Prohibited Sensitive Keywords that should NEVER be stored
    FORBIDDEN_CREDENTIAL_TERMS = [
        "otp", "one-time password", "upi pin", "mpin", 
        "cvv", "cvv2", "atm pin", "debit card pin",
        "netbanking password", "internet banking password", "transaction pin"
    ]

settings = Settings()
