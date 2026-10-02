"""
MedResearch AI — Configuration Loader

Loads settings from (in order):
  1. Streamlit secrets    (cloud deployment — .streamlit/secrets.toml or cloud UI)
  2. Environment variables / .env file    (local development)
  3. Defaults

This makes the same code work both locally and on Streamlit Cloud.
"""

import os
from pathlib import Path
from typing import Optional, Any

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


# ============================================================
# LOAD .env EARLY (local dev fallback)
# ============================================================

_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()  # default search


# ============================================================
# HELPER: read a key from Streamlit secrets OR env
# ============================================================

def _get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Look up a config value in this priority order:
      1. Streamlit secrets (cloud)
      2. Environment variables / .env (local)
      3. Provided default
    """
    # Try Streamlit secrets (only available when running in Streamlit)
    try:
        import streamlit as st
        # `st.secrets` raises if no secrets file exists
        if key in st.secrets:
            value = st.secrets[key]
            return str(value) if value is not None else default
    except Exception:
        pass

    # Fall back to env / .env
    value = os.environ.get(key)
    if value is not None:
        return value

    return default


# ============================================================
# SETTINGS
# ============================================================

class Settings(BaseSettings):
    """Application settings — loaded from Streamlit secrets or .env."""

    # --- API Keys ---
    groq_api_key: str = ""
    openrouter_api_key: str = ""
    tavily_api_key: str = ""
    pubmed_email: str = "test@example.com"

    # --- App ---
    app_name: str = "MedResearch AI"
    app_version: str = "0.1.0"
    debug: bool = False

    # --- Models ---
    primary_model: str = "openai/gpt-oss-120b"
    vision_model: str = "openai/gpt-oss-20b"
    temperature: float = 0.2
    max_tokens: int = 2000

    # --- Governance ---
    min_confidence: float = 0.7
    min_sources_per_claim: int = 1
    max_refusal_rate: float = 0.3

    # --- Vector DB ---
    chroma_persist_dir: str = "./chroma_db"

    # --- Paths ---
    base_dir: Path = Path(__file__).resolve().parent.parent

    class Config:
        env_file = ".env"
        extra = "ignore"
        case_sensitive = False


# ============================================================
# SINGLETON LOADER
# ============================================================

_settings_instance: Optional[Settings] = None


def _build_settings() -> Settings:
    """
    Build a Settings instance from Streamlit secrets + env vars.
    Explicitly pulls each key so we can fall back cleanly.
    """
    return Settings(
        groq_api_key=_get_secret("GROQ_API_KEY", "") or "",
        openrouter_api_key=_get_secret("OPENROUTER_API_KEY", "") or "",
        tavily_api_key=_get_secret("TAVILY_API_KEY", "") or "",
        pubmed_email=_get_secret("PUBMED_EMAIL", "test@example.com") or "test@example.com",
        app_name=_get_secret("APP_NAME", "MedResearch AI") or "MedResearch AI",
        app_version=_get_secret("APP_VERSION", "0.1.0") or "0.1.0",
        debug=str(_get_secret("DEBUG", "False")).lower() in ("1", "true", "yes"),
        primary_model=_get_secret("PRIMARY_MODEL", "openai/gpt-oss-120b") or "openai/gpt-oss-120b",
        vision_model=_get_secret("VISION_MODEL", "openai/gpt-oss-20b") or "openai/gpt-oss-20b",
        temperature=float(_get_secret("TEMPERATURE", "0.2") or 0.2),
        max_tokens=int(_get_secret("MAX_TOKENS", "2000") or 2000),
        min_confidence=float(_get_secret("MIN_CONFIDENCE", "0.7") or 0.7),
        min_sources_per_claim=int(_get_secret("MIN_SOURCES_PER_CLAIM", "1") or 1),
        max_refusal_rate=float(_get_secret("MAX_REFUSAL_RATE", "0.3") or 0.3),
        chroma_persist_dir=_get_secret("CHROMA_PERSIST_DIR", "./chroma_db") or "./chroma_db",
    )


def get_settings() -> Settings:
    """Get application settings (singleton)."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = _build_settings()
    return _settings_instance