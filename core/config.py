"""
MedResearch AI — Configuration Loader
Loads environment variables and validates settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field


# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # API Keys
    groq_api_key: str = Field(..., env="GROQ_API_KEY")
    tavily_api_key: str = Field(..., env="TAVILY_API_KEY")
    pubmed_email: str = Field(default="test@example.com", env="PUBMED_EMAIL")

    # App
    app_name: str = Field(default="MedResearch AI", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=True, env="DEBUG")

    # Models
    primary_model: str = Field(default="llama-3.3-70b-versatile", env="PRIMARY_MODEL")
    vision_model: str = Field(default="llama-3.2-90b-vision-preview", env="VISION_MODEL")
    temperature: float = Field(default=0.2, env="TEMPERATURE")
    max_tokens: int = Field(default=2000, env="MAX_TOKENS")

    # Governance
    min_confidence: float = Field(default=0.7, env="MIN_CONFIDENCE")
    min_sources_per_claim: int = Field(default=1, env="MIN_SOURCES_PER_CLAIM")
    max_refusal_rate: float = Field(default=0.3, env="MAX_REFUSAL_RATE")

    # Vector DB
    chroma_persist_dir: str = Field(default="./chroma_db", env="CHROMA_PERSIST_DIR")

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent

    class Config:
        env_file = ".env"
        extra = "ignore"


# Singleton
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings