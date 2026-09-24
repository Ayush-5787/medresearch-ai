"""
MedResearch AI — Web Search Tool
Tavily-powered web search for medical research.
"""

from tavily import TavilyClient
from typing import List, Dict, Optional
from core.config import get_settings


class WebSearchTool:
    """Tavily web search wrapper."""

    def __init__(self):
        self.settings = get_settings()
        self.client = TavilyClient(api_key=self.settings.tavily_api_key)

    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced",
        include_domains: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Search the web using Tavily."""
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_domains=include_domains or [
                    "pubmed.ncbi.nlm.nih.gov",
                    "nih.gov",
                    "who.int",
                    "cdc.gov",
                    "mayoclinic.org",
                    "webmd.com",
                    "healthline.com",
                    "medicalnewstoday.com",
                ],
            )

            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                    "score": r.get("score", 0.0),
                }
                for r in response.get("results", [])
            ]
        except Exception as e:
            print(f"[WebSearch] Error: {e}")
            return []


# Singleton
_search_tool: Optional[WebSearchTool] = None


def get_web_search() -> WebSearchTool:
    """Get web search tool singleton."""
    global _search_tool
    if _search_tool is None:
        _search_tool = WebSearchTool()
    return _search_tool