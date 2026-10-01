"""
MedResearch AI — Country Configuration
Provides country-specific data: languages, emergency numbers, trusted sources.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class CountryConfig:
    """Loads and manages country-specific configuration."""

    def __init__(self):
        self.data_path = Path(__file__).parent.parent / "data" / "countries.json"
        self._data: Dict = {}
        self._load()

    def _load(self):
        """Load countries from JSON file."""
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            print(f"[CountryConfig] Loaded {len(self._data)} countries")
        except FileNotFoundError:
            print(f"[CountryConfig] File not found: {self.data_path}")
            print("[CountryConfig] Using empty config")
            self._data = {}
        except Exception as e:
            print(f"[CountryConfig] Error loading: {e}")
            self._data = {}

    def get(self, country_code: str) -> dict:
        """Get configuration for a country (falls back to DEFAULT)."""
        code = (country_code or "").upper()
        return self._data.get(code, self._data.get("DEFAULT", {}))

    def get_languages(self, country_code: str) -> List[str]:
        """Get supported languages for a country."""
        return self.get(country_code).get("languages", ["en"])

    def get_emergency(self, country_code: str) -> str:
        """Get emergency number for a country."""
        return self.get(country_code).get("emergency", "112")

    def get_trusted_sources(self, country_code: str) -> List[dict]:
        """Get trusted sources for a country."""
        return self.get(country_code).get("trusted_sources", [])

    def list_countries(self) -> List[dict]:
        """List all supported countries."""
        result = []
        for code, config in self._data.items():
            if code == "DEFAULT":
                continue
            result.append({
                "code": code,
                "name": config.get("name", code),
                "languages": config.get("languages", ["en"]),
            })
        return sorted(result, key=lambda x: x["name"])


print("[country] CountryConfig loaded")