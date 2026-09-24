"""
MedResearch AI — URL Scraper
Extract clean text content from URLs.
"""

import httpx
from bs4 import BeautifulSoup
from typing import Optional
from urllib.parse import urlparse


class URLScraper:
    """Scrape and clean text from web pages."""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def scrape(self, url: str, max_chars: int = 5000) -> Optional[str]:
        """Scrape URL and return clean text."""
        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()

                text = soup.get_text(separator=" ", strip=True)
                text = " ".join(text.split())

                return text[:max_chars]

        except Exception as e:
            print(f"[Scraper] Error scraping {url}: {e}")
            return None

    def get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            return urlparse(url).netloc
        except Exception:
            return ""


# Singleton
_scraper: Optional[URLScraper] = None


def get_scraper() -> URLScraper:
    """Get scraper singleton."""
    global _scraper
    if _scraper is None:
        _scraper = URLScraper()
    return _scraper