"""
MedResearch AI — PubMed Search Tool
Queries NCBI E-utilities API for real medical literature.
Free, no API key required (rate limit: 3 req/sec).
"""

import httpx
from typing import List, Dict, Optional
from xml.etree import ElementTree as ET
from core.config import get_settings
from core.schemas import Source


class PubMedSearch:
    """Search PubMed for medical papers via NCBI E-utilities."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self):
        self.settings = get_settings()
        self.email = self.settings.pubmed_email
        self.timeout = 20

    async def search_ids(self, query: str, max_results: int = 10) -> List[str]:
        """Step 1: Search PubMed for article IDs (PMIDs)."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}/esearch.fcgi",
                    params={
                        "db": "pubmed",
                        "term": query,
                        "retmax": max_results,
                        "retmode": "json",
                        "email": self.email,
                        "sort": "relevance",
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data.get("esearchresult", {}).get("idlist", [])
        except Exception as e:
            print(f"[PubMed] Search error: {e}")
            return []

    async def fetch_details(self, pmids: List[str]) -> List[Source]:
        """Step 2: Fetch full details for each PMID."""
        if not pmids:
            return []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}/efetch.fcgi",
                    params={
                        "db": "pubmed",
                        "id": ",".join(pmids),
                        "retmode": "xml",
                        "email": self.email,
                    },
                )
                response.raise_for_status()
                root = ET.fromstring(response.text)

                sources = []
                for article in root.findall(".//PubmedArticle"):
                    pmid = article.findtext(".//PMID") or ""
                    title = article.findtext(".//ArticleTitle") or ""
                    abstract = self._extract_abstract(article)
                    journal = article.findtext(".//Journal/Title") or ""
                    year = self._extract_year(article)
                    authors = self._extract_authors(article)

                    if not title:
                        continue

                    sources.append(
                        Source(
                            url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                            title=title,
                            snippet=abstract[:1500] if abstract else title,
                            source_type="pubmed",
                            credibility_score=0.9,  # PubMed = high trust
                            pmid=pmid,
                            authors=authors,
                            year=year,
                            journal=journal,
                        )
                    )
                return sources
        except Exception as e:
            print(f"[PubMed] Fetch error: {e}")
            return []

    def _extract_abstract(self, article) -> str:
        """Extract abstract text from XML."""
        parts = article.findall(".//AbstractText")
        return " ".join([(p.text or "").strip() for p in parts if p.text])

    def _extract_year(self, article) -> Optional[str]:
        """Extract publication year."""
        year = article.findtext(".//PubDate/Year")
        if not year:
            medline_date = article.findtext(".//PubDate/MedlineDate")
            if medline_date:
                year = medline_date.split(" ")[0]
        return year

    def _extract_authors(self, article) -> List[str]:
        """Extract author names."""
        authors = []
        for author in article.findall(".//Author")[:5]:
            last = author.findtext("LastName") or ""
            first = author.findtext("ForeName") or ""
            if last:
                authors.append(f"{last} {first}".strip())
        return authors

    async def full_search(self, query: str, max_results: int = 10) -> List[Source]:
        """Complete pipeline: search → fetch."""
        pmids = await self.search_ids(query, max_results)
        if not pmids:
            print(f"[PubMed] No results for: {query}")
            return []
        return await self.fetch_details(pmids)


print("[pubmed_search] PubMedSearch loaded")