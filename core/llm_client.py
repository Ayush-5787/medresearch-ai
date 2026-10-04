"""
Provider-agnostic LLM client with failover.

Design notes (report-ready):
- Providers are configuration, not code: base_url + model + key_env.
- 429 = quota exhausted -> fail over IMMEDIATELY (retrying cannot help
  within the quota window; the old 3x-retry-then-failover wasted ~10s/call).
- Transient errors (5xx, timeouts, connection) -> retry with backoff.
- Every failure increments a global counter read by the eval harness, so
  any case touched by infrastructure errors is flagged `contaminated`.
"""

import os
import time
import random
import threading
from openai import OpenAI, RateLimitError, APIConnectionError, APITimeoutError

# ----------------------------------------------------------------------
# Provider registry — order comes from env so evals can run Gemini-first
# ----------------------------------------------------------------------
PROVIDER_REGISTRY = {
    "groq": {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "model": "openai/gpt-oss-120b",   # VERIFY in Groq console — Llama left free tier Aug 2026
        "key_env": "GROQ_API_KEY",
    },
    "gemini": {
        "name": "Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-2.5-flash",      # VERIFY exact ID in AI Studio before running
        "key_env": "GEMINI_API_KEY",
    },
}
DEFAULT_ORDER = "groq,gemini"


class LLMError(Exception):
    """Raised when every provider in the chain failed."""


# ----------------------------------------------------------------------
# Global instrumentation — consumed by run_evals.py
# ----------------------------------------------------------------------
_lock = threading.Lock()
_stats = {"llm_error_count": 0, "failovers": 0}

def get_llm_stats() -> dict:
    with _lock:
        return dict(_stats)

def reset_llm_stats() -> None:
    with _lock:
        _stats.update(llm_error_count=0, failovers=0)

def _bump(field: str) -> None:
    with _lock:
        _stats[field] += 1


class LLMClient:
    def __init__(self, order: str = None, max_transient_retries: int = 3):
        order = order or os.getenv("LLM_PROVIDER_ORDER", DEFAULT_ORDER)
        self.max_transient_retries = max_transient_retries
        self.chain = []
        for key in [k.strip().lower() for k in order.split(",") if k.strip()]:
            spec = PROVIDER_REGISTRY.get(key)
            if spec is None:
                raise ValueError(f"Unknown provider '{key}' in LLM_PROVIDER_ORDER")
            api_key = os.getenv(spec["key_env"])
            if not api_key:
                print(f"[LLM] ⚠️ {spec['key_env']} not set — skipping {spec['name']}")
                continue
            self.chain.append({**spec,
                               "client": OpenAI(base_url=spec["base_url"], api_key=api_key)})
        if not self.chain:
            raise RuntimeError("No LLM provider configured — check .env keys")
        print(f"[LLM] Chain: {' → '.join(p['name'] for p in self.chain)}")

    def chat(self, messages, temperature=0.2, max_tokens=1024, json_mode=False):
        """Returns the OpenAI-compatible response object (same shape as before)."""
        last_errors = []
        for provider in self.chain:
            try:
                return self._call_with_retries(provider, messages, temperature,
                                               max_tokens, json_mode)
            except RateLimitError:
                _bump("failovers")
                print(f"[LLM] ⚠️ {provider['name']} quota/429 → failing over immediately")
                last_errors.append(f"{provider['name']}: 429")
                continue
            except (APIConnectionError, APITimeoutError) as e:
                _bump("llm_error_count")
                print(f"[LLM] ⚠️ {provider['name']} network error: {e}")
                last_errors.append(f"{provider['name']}: {type(e).__name__}")
                continue
            except Exception as e:
                _bump("llm_error_count")
                print(f"[LLM] ⚠️ {provider['name']} failed: {e}")
                last_errors.append(f"{provider['name']}: {e}")
                continue
        raise LLMError("All LLM providers failed. " + " | ".join(last_errors))

    def _call_with_retries(self, provider, messages, temperature, max_tokens, json_mode):
        delay = 1.0
        for attempt in range(1, self.max_transient_retries + 1):
            try:
                kwargs = dict(model=provider["model"], messages=messages,
                              temperature=temperature, max_tokens=max_tokens)
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                return provider["client"].chat.completions.create(**kwargs)
            except RateLimitError:
                raise  # quota → no point retrying here; caller fails over
            except (APIConnectionError, APITimeoutError) as e:
                if attempt < self.max_transient_retries:
                    wait = delay + random.uniform(0, 0.5)
                    print(f"[LLM] Retry {attempt}/{self.max_transient_retries} "
                          f"on {provider['name']} after {wait:.1f}s (transient)")
                    time.sleep(wait)
                    delay = min(delay * 2, 30)
                    continue
                raise