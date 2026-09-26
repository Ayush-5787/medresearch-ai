"""
MedResearch AI — Test Writer Agent
Runs the full Search → Reader → Writer pipeline.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.search_agent import SearchAgent
from agents.reader_agent import ReaderAgent
from agents.writer_agent import WriterAgent


async def main():
    print("=" * 60)
    print("TESTING SEARCH + READER + WRITER PIPELINE")
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

    # Display final answer
    print("\n" + "=" * 60)
    print("FINAL ANSWER")
    print("=" * 60)
    print()
    print(answer.answer)
    print()
    print("-" * 60)
    print("REFERENCES")
    print("-" * 60)
    for i, src in enumerate(answer.sources, 1):
        print(f"[{i}] {src.url}")
    print()
    print("-" * 60)
    print("METADATA")
    print("-" * 60)
    print(f"  Status:      {answer.status}")
    print(f"  Confidence:  {answer.confidence:.2f}")
    print(f"  Claims used: {len(answer.claims)}")
    print(f"  Sources:     {len(answer.sources)}")
    print(f"  Disclaimer:  {answer.disclaimer[:80]}...")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())