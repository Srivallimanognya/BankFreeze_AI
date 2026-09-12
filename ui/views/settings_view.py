"""
Settings View for BankFreeze AI
Controls LLM provider configuration, mock adapter simulation parameters,
and demo database re-seeding / reset tools.
"""

import streamlit as st
from sqlalchemy.orm import Session

from config.settings import settings
from modules.llm_service import llm_service
from database.connection import reset_db
from demo.seed_data import seed_database
from modules.audit import log_audit

def render_settings_view(db: Session):
    st.markdown("## ⚙️ System Configuration & Diagnostics")
    st.caption("Manage LLM inference parameters, mock simulation speeds, and demonstration data fixtures.")

    tab_llm, tab_adapters, tab_db = st.tabs(["🤖 LLM Integration", "🔌 Mock Adapters", "💾 Database & Fixtures"])

    with tab_llm:
        st.markdown("### OpenAI-Compatible LLM Settings")
        st.caption("BankFreeze AI operates fully offline using deterministic heuristics. You may optionally connect any OpenAI-compatible endpoint.")

        curr_key = st.text_input("API Key", value=settings.OPENAI_API_KEY, type="password", placeholder="sk-...")
        curr_base = st.text_input("API Base URL", value=settings.OPENAI_API_BASE)
        curr_model = st.text_input("Model Identifier", value=settings.LLM_MODEL)
        curr_temp = st.slider("Temperature", min_value=0.0, max_value=1.0, value=settings.LLM_TEMPERATURE, step=0.05)

        col_save, col_test = st.columns([1, 1])
        with col_save:
            if st.button("Save Settings 💾", use_container_width=True):
                settings.OPENAI_API_KEY = curr_key
                settings.OPENAI_API_BASE = curr_base
                settings.LLM_MODEL = curr_model
                settings.LLM_TEMPERATURE = curr_temp
                st.success("LLM configuration updated in active session!")
        with col_test:
            if st.button("Test LLM Connection ⚡", use_container_width=True):
                if not curr_key:
                    st.warning("No API key configured. Offline heuristic engine active.")
                else:
                    settings.OPENAI_API_KEY = curr_key
                    settings.OPENAI_API_BASE = curr_base
                    settings.LLM_MODEL = curr_model
                    res = llm_service.complete("Respond with 'OK' if you receive this message.")
                    if res:
                        st.success(f"Connection Successful! Response: {res}")
                    else:
                        st.error("Connection failed. Check your API key and base URL.")

    with tab_adapters:
        st.markdown("### Mock Adapter Latency Emulation")
        st.caption("Simulate network roundtrips to Core Banking Systems and Law Enforcement Registries.")

        bank_lat = st.slider("Mock Bank API Latency (seconds)", 0.0, 3.0, settings.MOCK_BANK_LATENCY, 0.1)
        auth_lat = st.slider("Mock Authority API Latency (seconds)", 0.0, 3.0, settings.MOCK_AUTHORITY_LATENCY, 0.1)

        if st.button("Apply Latency Parameters 💾"):
            settings.MOCK_BANK_LATENCY = bank_lat
            settings.MOCK_AUTHORITY_LATENCY = auth_lat
            st.success("Adapter latency updated.")

    with tab_db:
        st.markdown("### Demonstration Data Fixtures & Reset")
        st.warning("⚠️ These operations affect all stored cases, documents, and audit logs.")

        c_seed, c_wipe = st.columns(2)
        with c_seed:
            if st.button("🔄 Re-Seed 5 Demo Cases", use_container_width=True):
                seed_database()
                st.success("Demo cases verified and seeded!")
                st.rerun()

        with c_wipe:
            confirm_wipe = st.checkbox("Confirm database wipe and fresh re-seed")
            if confirm_wipe:
                if st.button("⚠️ Wipe Database & Rebuild", use_container_width=True):
                    reset_db()
                    seed_database()
                    st.success("Database cleanly re-initialized with 5 standard demo cases!")
                    st.rerun()
