"""
MedResearch AI — LLM Wrapper
Multi-provider LLM interface with automatic fallback.

Chain:
  1. Groq (primary)        — fast, reliable, 200K tokens/day
  2. OpenRouter (fallback) — free Llama 3.3 70B

Both providers are called via OpenAI-compatible APIs, so the
request/response shape is identical.
"""

import os
import time
from typing import List, Dict, Optional

from groq import Groq
from openai import OpenAI

from core.config import get_settings


class LLMClient:
    """Wrapper around Groq + OpenRouter with retry and fallback."""

    def __init__(self):
        self.settings = get_settings()
        self.model = self.settings.primary_model
        self.temperature = self.settings.temperature
        self.max_tokens = self.settings.max_tokens

        # ----------------------------------------------------------
        # Initialize provider clients
        # ----------------------------------------------------------
        self._providers: Dict[str, Dict] = {}

        # Groq (primary)
        groq_key = getattr(self.settings, "groq_api_key", None) or os.environ.get("GROQ_API_KEY")
        if groq_key:
            self._providers["groq"] = {
                "client": Groq(api_key=groq_key),
                "model": self.model,  # e.g. "openai/gpt-oss-120b"
                "label": "Groq",
            }

        # OpenRouter (fallback) — OpenAI SDK
        or_key = os.environ.get("OPENROUTER_API_KEY")
        if or_key:
            self._providers["openrouter"] = {
                "client": OpenAI(
                    api_key=or_key,
                    base_url="https://openrouter.ai/api/v1",
                ),
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "label": "OpenRouter (Llama 3.3)",
            }

        if not self._providers:
            raise RuntimeError(
                "No LLM providers configured. "
                "Set GROQ_API_KEY and/or OPENROUTER_API_KEY in .env."
            )

        # Order: Groq first, OpenRouter as fallback
        self.provider_chain = [k for k in ["groq", "openrouter"] if k in self._providers]

    # ----------------------------------------------------------
    # PROVIDER CALL
    # ----------------------------------------------------------

    def _call_provider(
        self,
        provider_name: str,
        messages: List[Dict[str, str]],
        model: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call a single provider and return the text content."""
        p = self._providers[provider_name]
        response = p["client"].chat.completions.create(
            model=model or p["model"],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    # ----------------------------------------------------------
    # PUBLIC API
    # ----------------------------------------------------------

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_retries: int = 3,
    ) -> str:
        """
        Send a chat request with automatic provider fallback.

        Tries each provider in provider_chain in order.
        Retries each provider max_retries times with exponential backoff.
        Falls back to the next provider on failure.
        """
        temp = temperature if temperature is not None else self.temperature
        mt = max_tokens or self.max_tokens
        last_error = None

        for provider_name in self.provider_chain:
            p = self._providers[provider_name]

            for attempt in range(max_retries):
                try:
                    content = self._call_provider(
                        provider_name, messages, model, temp, mt
                    )
                    # Only announce when a fallback happened (avoid log spam)
                    if provider_name != "groq" or attempt > 0:
                        print(f"[LLM] ✅ {p['label']} succeeded")
                    return content

                except Exception as e:
                    last_error = e

                    if attempt == max_retries - 1:
                        print(
                            f"[LLM] ⚠️ {p['label']} failed after {max_retries} tries: "
                            f"{str(e)[:120]}"
                        )
                        break

                    wait = 2 ** attempt
                    print(
                        f"[LLM] Retry {attempt + 1}/{max_retries} on {p['label']} "
                        f"after {wait}s: {str(e)[:100]}"
                    )
                    time.sleep(wait)

            # Move to the next provider in the chain
            if provider_name != self.provider_chain[-1]:
                print(f"[LLM] → Falling back from {p['label']}...")

        raise RuntimeError(
            f"All LLM providers failed. Last error: {str(last_error)[:200]}"
        )

    def simple(
        self,
        prompt: str,
        system: str = "You are a helpful assistant.",
    ) -> str:
        """Simple single-turn completion."""
        return self.chat([
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ])


# ==============================================================
# SINGLETON
# ==============================================================

_llm_client: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    """Get LLM client singleton."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client