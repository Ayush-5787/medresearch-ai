"""
MedResearch AI — Search Agent
Combines PubMed + Tavily web search, deduplicates and ranks results.
"""

import asyncio
from typing import List
from agents.base_agent import BaseAgent, Timer
from tools.pubmed_search import PubMedSearch
from tools.web_search import get_web_search
from core.schemas import Source, SearchResult


class SearchAgent(BaseAgent):
    """The first agent: finds evidence from PubMed + web."""

    def __init__(self):
        super().__init__(name="SearchAgent")
        self.pubmed = PubMedSearch()
        self.web = get_web_search()

    async def run(self, question: str, pubmed_max: int = 8, web_max: int = 5) -> SearchResult:
        """
        Search PubMed + web in parallel, merge, deduplicate, rank.
        """
        self.clear_trace()
        self.log_step("start", question, "beginning search")

        # Run PubMed and web searches in parallel
        with Timer() as t:
            pubmed_task = self.pubmed.full_search(question, max_results=pubmed_max)
            web_task = asyncio.to_thread(self.web.search, question, max_results=web_max)
            pubmed_sources, web_sources = await asyncio.gather(pubmed_task, web_task)

        self.log_step(
            "search_complete",
            f"pubmed_max={pubmed_max}, web_max={web_max}",
            f"pubmed={len(pubmed_sources)}, web={len(web_sources)}",
            t.elapsed_ms,
        )

        # Convert web results to Source objects
        web_as_sources = [
            Source(
                url=r["url"],
                title=r["title"],
                snippet=r["content"][:1000],
                source_type="web",
                credibility_score=self._score_domain(r["url"]),
            )
            for r in web_sources
            if r.get("url")
        ]

        # Merge + deduplicate by URL
        all_sources = self._dedupe(pubmed_sources + web_as_sources)

        # Sort by credibility score (higher first)
        all_sources.sort(key=lambda s: s.credibility_score, reverse=True)

        self.log_step(
            "ranked",
            f"{len(all_sources)} total sources",
            f"top: {all_sources[0].title[:60] if all_sources else 'none'}",
        )

        return SearchResult(
            question=question,
            sources=all_sources,
            pubmed_count=len(pubmed_sources),
            web_count=len(web_as_sources),
            agent_trace=self.trace.copy(),
        )

    def _dedupe(self, sources: List[Source]) -> List[Source]:
        """Remove duplicate URLs."""
        seen = set()
        unique = []
        for s in sources:
            if s.url and s.url not in seen:
                seen.add(s.url)
                unique.append(s)
        return unique

    def _score_domain(self, url: str) -> float:
        """Assign credibility score based on domain."""
        url_lower = url.lower()
        if any(d in url_lower for d in ["pubmed", "nih.gov", "who.int", "cdc.gov"]):
            return 0.95
        if any(d in url_lower for d in ["mayoclinic.org", "clevelandclinic.org"]):
            return 0.85
        if any(d in url_lower for d in ["webmd.com", "healthline.com", "medicalnewstoday.com"]):
            return 0.7
        return 0.5  # Unknown domain


print("[search_agent] SearchAgent loaded")