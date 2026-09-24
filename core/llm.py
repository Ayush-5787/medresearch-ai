"""
MedResearch AI — LLM Wrapper
Groq-powered LLM interface with retry logic.
"""

from groq import Groq
from typing import List, Dict, Optional
import time
from core.config import get_settings


class LLMClient:
    """Wrapper around Groq LLM with retry and logging."""

    def __init__(self):
        self.settings = get_settings()
        self.client = Groq(api_key=self.settings.groq_api_key)
        self.model = self.settings.primary_model
        self.temperature = self.settings.temperature
        self.max_tokens = self.settings.max_tokens

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_retries: int = 3,
    ) -> str:
        """Send a chat request to Groq with retry logic."""
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=model or self.model,
                    messages=messages,
                    temperature=temperature if temperature is not None else self.temperature,
                    max_tokens=max_tokens or self.max_tokens,
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait = 2 ** attempt
                print(f"[LLM] Retry {attempt + 1}/{max_retries} after {wait}s: {e}")
                time.sleep(wait)

        return ""

    def simple(self, prompt: str, system: str = "You are a helpful assistant.") -> str:
        """Simple single-turn completion."""
        return self.chat([
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ])


# Singleton
_llm_client: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    """Get LLM client singleton."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client