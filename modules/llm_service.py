"""
LLM Service Module for BankFreeze AI
Supports OpenAI-compatible LLM endpoints with an intelligent deterministic fallback heuristic engine.
Ensures zero-crash execution even without an API key or when offline.
"""

import json
import logging
from typing import Dict, Any, Optional, List
import httpx

from config.settings import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.api_base = settings.OPENAI_API_BASE.rstrip("/")
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE

    def is_configured(self) -> bool:
        """Check if an active API key is provided."""
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def complete(self, prompt: str, system_prompt: Optional[str] = None, json_mode: bool = False) -> str:
        """
        Execute an LLM chat completion.
        If an API key is present, calls the OpenAI-compatible REST API.
        Otherwise, returns empty string so heuristic fallbacks take over gracefully.
        """
        if not self.is_configured():
            logger.info("LLM not configured with API key. Falling back to heuristic engine.")
            return ""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload
                )
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.warning(f"LLM API returned status {response.status_code}: {response.text}")
                    return ""
        except Exception as e:
            logger.warning(f"Error calling LLM API: {e}. Falling back to heuristic engine.")
            return ""

llm_service = LLMService()
