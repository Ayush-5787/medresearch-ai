"""
MedResearch AI — Reader Agent
Reads sources and extracts structured medical claims.
"""

import asyncio
import json
from typing import List
from agents.base_agent import BaseAgent, Timer
from tools.scrape_url import get_scraper
from core.schemas import Source, Claim, SearchResult


class ReaderAgent(BaseAgent):
    """
    Reads each source and extracts factual claims.
    Each claim is tagged with its source URL for traceability.
    """

    EXTRACTION_PROMPT = """You are a medical fact extractor. Read the following text and extract ONLY factual medical claims that are directly stated.

RULES:
1. Extract 1-5 claims maximum per source.
2. Each claim must be a complete, self-contained sentence.
3. Do NOT add information not present in the text.
4. Do NOT make medical recommendations.
5. If the text has no medical facts, return an empty list.
6. Return ONLY valid JSON, no other text.

Output format (JSON array):
[
  {{"claim": "Metformin commonly causes gastrointestinal side effects.", "confidence": 0.9}},
  {{"claim": "Lactic acidosis is a rare but serious side effect.", "confidence": 0.85}}
]

Text to analyze:
---
{text}
---

JSON output:"""

    def __init__(self):
        super().__init__(name="ReaderAgent")
        self.scraper = get_scraper()
        self.max_chars_per_source = 4000
        self.max_sources_to_read = 6

    async def run(self, search_result: SearchResult) -> List[Claim]:
        """Read sources and extract claims."""
        self.clear_trace()
        self.log_step(
            "start",
            f"{len(search_result.sources)} sources",
            "beginning extraction",
        )

        # Only read top N sources (by credibility)
        sources = search_result.sources[: self.max_sources_to_read]

        # Process sources in parallel
        with Timer() as t:
            tasks = [self._extract_from_source(s) for s in sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results
        all_claims: List[Claim] = []
        for src, result in zip(sources, results):
            if isinstance(result, Exception):
                self.log_step(
                    "error",
                    src.url[:60],
                    f"extraction failed: {str(result)[:100]}",
                )
                continue
            all_claims.extend(result)

        self.log_step(
            "extraction_complete",
            f"{len(sources)} sources processed",
            f"{len(all_claims)} claims extracted",
            t.elapsed_ms,
        )

        # Deduplicate similar claims
        unique_claims = self._dedupe_claims(all_claims)

        self.log_step(
            "deduplicated",
            f"{len(all_claims)} raw claims",
            f"{len(unique_claims)} unique claims",
        )

        return unique_claims

    async def _extract_from_source(self, source: Source) -> List[Claim]:
        """Extract claims from a single source."""
        # Get text — use snippet for PubMed, scrape for web
        if source.source_type == "pubmed":
            text = source.snippet
        else:
            text = await asyncio.to_thread(self.scraper.scrape, source.url)

        if not text:
            return []

        # Truncate
        text = text[: self.max_chars_per_source]

        # Ask LLM to extract claims
        try:
            response = self.llm.simple(
                self.EXTRACTION_PROMPT.format(text=text),
                system="You extract medical facts and return only JSON.",
            )

            facts = self._parse_json_response(response)

            claims = [
                Claim(
                    text=f["claim"].strip(),
                    source_urls=[source.url],
                    confidence=float(f.get("confidence", 0.7)),
                    verified=False,
                )
                for f in facts
                if isinstance(f, dict) and f.get("claim")
            ]

            self.log_step(
                "extracted",
                f"{source.source_type}: {source.title[:50]}",
                f"{len(claims)} claims",
            )
            return claims

        except Exception as e:
            print(f"[ReaderAgent] LLM error on {source.url[:50]}: {e}")
            return []

    def _parse_json_response(self, response: str) -> list:
        """Safely parse JSON from LLM response."""
        response = response.strip()

        # Remove markdown code fences if present
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
            response = response.strip()

        # Find first [ and last ]
        start = response.find("[")
        end = response.rfind("]")
        if start == -1 or end == -1:
            return []

        try:
            data = json.loads(response[start : end + 1])
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    def _dedupe_claims(self, claims: List[Claim]) -> List[Claim]:
        """Remove near-duplicate claims (case-insensitive, first 60 chars)."""
        seen = set()
        unique = []
        for c in claims:
            key = " ".join(c.text.lower().split())[:60]
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique


print("[reader_agent] ReaderAgent loaded")