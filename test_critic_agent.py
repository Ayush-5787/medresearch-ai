"""
MedResearch AI — Test Critic Agent
Runs the full Search → Read → Write → Critique pipeline.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.search_agent import SearchAgent
from agents.reader_agent import ReaderAgent
from agents.writer_agent import WriterAgent
from agents.critic_agent import CriticAgent


async def main():
    print("=" * 60)
    print("TESTING SEARCH + READER + WRITER + CRITIC PIPELINE")
    print("=" * 60)
    print()

    question = "What are the side effects of metformin?"

    # Stage 1: Search
    print("STAGE 1: Search")
    print("-" * 60)
    search_agent = SearchAgent()
    search_result = await search_agent.run(question)
    print(f"Found {len(search_result.sources)} sources\n")

    # Stage 2: Read
    print("STAGE 2: Read")
    print("-" * 60)
    reader_agent = ReaderAgent()
    claims = await reader_agent.run(search_result)
    print(f"Extracted {len(claims)} claims\n")

    # Stage 3: Write
    print("STAGE 3: Write")
    print("-" * 60)
    writer_agent = WriterAgent()
    answer = await writer_agent.run(question, claims)
    print(f"Drafted {len(answer.answer)} chars\n")

    # Stage 4: Critique
    print("STAGE 4: Critique")
    print("-" * 60)
    critic_agent = CriticAgent()
    critique = await critic_agent.run(answer, original_claims=claims)

    # Display critique
    print("\n" + "=" * 60)
    print("CRITIQUE RESULT")
    print("=" * 60)
    print()
    print(f"  Status:  {critique.status}")
    print(f"  Score:   {critique.overall_score:.2f}")
    print(f"  Summary: {critique.reasoning_summary}")
    print()
    print("-" * 60)
    print(f"ISSUES FOUND ({len(critique.issues)})")
    print("-" * 60)
    if not critique.issues:
        print("  No issues found.")
    for i, issue in enumerate(critique.issues, 1):
        print(f"\n[{i}] {issue.severity} — {issue.type}")
        print(f"    {issue.description}")
        if issue.suggested_fix:
            print(f"    Fix: {issue.suggested_fix}")
        if issue.draft_snippet:
            print(f"    Draft: {issue.draft_snippet[:80]}")
        if issue.source_snippet:
            print(f"    Source: {issue.source_snippet[:80]}")
    print()
    print("-" * 60)
    print("METRICS")
    print("-" * 60)
    for k, v in critique.metrics.items():
        print(f"  {k}: {v}")
    print()
    print("=" * 60)
    print("ORIGINAL ANSWER (for reference)")
    print("=" * 60)
    print()
    print(answer.answer[:500] + ("..." if len(answer.answer) > 500 else ""))
    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())