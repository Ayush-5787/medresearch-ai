"""
MedResearch AI — Test Reader Agent
Verifies Search + Reader pipeline end-to-end.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.search_agent import SearchAgent
from agents.reader_agent import ReaderAgent


async def main():
    print("=" * 60)
    print("TESTING SEARCH + READER PIPELINE")
    print("=" * 60)
    print()

    question = "What are the side effects of metformin?"

    # Stage 1: Search
    print("STAGE 1: Search")
    print("-" * 60)
    search_agent = SearchAgent()
    search_result = await search_agent.run(question)
    print(f"Found {len(search_result.sources)} sources "
          f"({search_result.pubmed_count} PubMed, {search_result.web_count} web)")

    # Stage 2: Read
    print("\nSTAGE 2: Read")
    print("-" * 60)
    reader_agent = ReaderAgent()
    claims = await reader_agent.run(search_result)

    # Show results
    print(f"\nEXTRACTED {len(claims)} CLAIMS")
    print("-" * 60)
    for i, c in enumerate(claims[:10], 1):
        print(f"\n[{i}] {c.text}")
        print(f"    Confidence: {c.confidence:.2f}")
        print(f"    Source: {c.source_urls[0]}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Sources found:     {len(search_result.sources)}")
    print(f"  Sources read:      {min(6, len(search_result.sources))}")
    print(f"  Claims extracted:  {len(claims)}")
    print(f"  Avg confidence:    "
          f"{sum(c.confidence for c in claims) / len(claims) if claims else 0:.2f}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())