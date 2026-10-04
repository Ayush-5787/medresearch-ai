"""
MedResearch AI — LLM Wrapper
Multi-provider LLM interface with automatic fallback.

Chain (configurable via LLM_PROVIDER_ORDER in .env):
  1. Groq   (primary)   — fast, no training on prompts (user-facing path)
  2. Gemini (fallback)  — Google AI Studio free tier (eval-heavy path)

History (report-ready):
- Original fallback was OpenRouter's free Llama 3.3 slug, which was retired
  silently — the chain was broken until the eval harness surfaced it.
- Lessons encoded here: (1) providers are configuration, not code;
  (2) HTTP 429 triggers IMMEDIATE failover, because retrying an exhausted
  quota cannot succeed within the window; (3) every failure increments a
  global counter so the eval harness can flag contaminated cases.
"""

import os
import time
import threading
from typing import List, Dict, Optional

from openai import OpenAI, RateLimitError, APIConnectionError, APITimeoutError

from core.config import get_settings


# ----------------------------------------------------------------------
# Provider registry — order comes from env so evals can run Gemini-first
# ----------------------------------------------------------------------
PROVIDER_REGISTRY = {
    "groq": {
        "label": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": None,            # uses settings.primary_model
        "model_env": None,
        "key_env": "GROQ_API_KEY",
    },
    "gemini": {
        "label": "Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "default_model": "gemini-2.5-flash",   # VERIFY exact ID in AI Studio
        "model_env": "GEMINI_MODEL",
        "key_env": "GEMINI_API_KEY",
    },
}
DEFAULT_ORDER = "groq,gemini"


# ----------------------------------------------------------------------
# Global instrumentation — consumed by evals/run_evals.py
# ----------------------------------------------------------------------
_lock = threading.Lock()
_stats = {"llm_error_count": 0, "failovers": 0}


def get_llm_stats() -> Dict[str, int]:
    with _lock:
        return dict(_stats)


def reset_llm_stats() -> None:
    with _lock:
        _stats.update(llm_error_count=0, failovers=0)


def _bump(field: str) -> None:
    with _lock:
        _stats[field] += 1


class LLMClient:
    """
    Wrapper around Groq + Gemini with retry, fast failover, and instrumentation.

    Public interface unchanged from the original:
      chat(messages, model=None, temperature=None, max_tokens=None, max_retries=3) -> str
      simple(prompt, system=...) -> str
    """

    def __init__(self):
        self.settings = get_settings()
        self.model = self.settings.primary_model
        self.temperature = self.settings.temperature
        self.max_tokens = self.settings.max_tokens

        # ----------------------------------------------------------
        # Build provider chain from env order
        # ----------------------------------------------------------
        self._providers: Dict[str, Dict] = {}

        order = os.environ.get("LLM_PROVIDER_ORDER", DEFAULT_ORDER)
        for key in [k.strip().lower() for k in order.split(",") if k.strip()]:
            spec = PROVIDER_REGISTRY.get(key)
            if spec is None:
                print(f"[LLM] ⚠️ Unknown provider '{key}' in LLM_PROVIDER_ORDER — skipping")
                continue

            api_key = (
                os.environ.get(spec["key_env"])
                or getattr(self.settings, spec["key_env"].lower(), None)
            )
            if not api_key:
                print(f"[LLM] ⚠️ {spec['key_env']} not set — skipping {spec['label']}")
                continue

            model = self.model
            if spec["model_env"]:
                model = os.environ.get(spec["model_env"]) or spec["default_model"]

            self._providers[key] = {
                "client": OpenAI(api_key=api_key, base_url=spec["base_url"]),
                "model": model,
                "label": spec["label"],
            }

        if not self._providers:
            raise RuntimeError(
                "No LLM providers configured. "
                "Set GROQ_API_KEY and/or GEMINI_API_KEY in .env."
            )

        self.provider_chain = [
            k for k in (s.strip().lower() for s in order.split(","))
            if k in self._providers
        ]
        print(f"[LLM] Chain: {' → '.join(self._providers[k]['label'] for k in self.provider_chain)}")

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

        - Transient errors (network, timeout, 5xx): retry with backoff.
        - 429 / quota errors: fail over to the next provider IMMEDIATELY.
        - Every failure increments the global stats counter.
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
                    if provider_name != self.provider_chain[0] or attempt > 0:
                        print(f"[LLM] ✅ {p['label']} succeeded")
                    return content

                except RateLimitError as e:
                    # 429 = quota exhausted. Retrying cannot succeed within
                    # the window — fall through to the next provider now.
                    last_error = e
                    _bump("failovers")
                    print(f"[LLM] ⚠️ {p['label']} quota/429 → failing over immediately")
                    break

                except (APIConnectionError, APITimeoutError) as e:
                    last_error = e
                    _bump("llm_error_count")
                    if attempt == max_retries - 1:
                        print(f"[LLM] ⚠️ {p['label']} failed after {max_retries} tries: {str(e)[:120]}")
                        break
                    wait = 2 ** attempt
                    print(f"[LLM] Retry {attempt + 1}/{max_retries} on {p['label']} after {wait}s (transient)")
                    time.sleep(wait)

                except Exception as e:
                    last_error = e
                    _bump("llm_error_count")
                    if attempt == max_retries - 1:
                        print(f"[LLM] ⚠️ {p['label']} failed after {max_retries} tries: {str(e)[:120]}")
                        break
                    wait = 2 ** attempt
                    print(f"[LLM] Retry {attempt + 1}/{max_retries} on {p['label']} after {wait}s: {str(e)[:100]}")
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