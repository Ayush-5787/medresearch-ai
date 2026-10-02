"""
MedResearch AI — Agents package.
Loads .env variables on import so all agents can read API keys.
"""

from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)