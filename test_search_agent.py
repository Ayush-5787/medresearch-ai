"""
MedResearch AI — Test Search Agent
Verifies PubMed + web search work end-to-end.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.search_agent import SearchAgent


async def main():
    print("=" * 60)
    print("TESTING SEARCH AGENT")
    print("=" * 60)
    print()

    agent = SearchAgent()

    questions = [
        "What are the side effects of metformin?",
        "How does COVID-19 affect the cardiovascular system?",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n--- Question {i}: {question} ---")
        result = await agent.run(question)

        print(f"\nRESULTS:")
        print(f"   Total sources: {len(result.sources)}")
        print(f"   From PubMed:   {result.pubmed_count}")
        print(f"   From Web:      {result.web_count}")

        print(f"\nTop 3 sources:")
        for j, src in enumerate(result.sources[:3], 1):
            print(f"   [{j}] ({src.source_type.upper()}, score={src.credibility_score:.2f})")
            print(f"       {src.title[:80]}")
            print(f"       {src.url}")

        print(f"\nAgent trace:")
        for step in result.agent_trace:
            print(f"   - {step.agent_name}: {step.action} ({step.duration_ms}ms)")

    print("\n" + "=" * 60)
    print("SEARCH AGENT TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())