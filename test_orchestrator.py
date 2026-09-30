"""
MedResearch AI — Test Orchestrator
Runs the full 6-agent pipeline via the orchestrator.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.orchestrator import MedResearchPipeline


async def main():
    print("=" * 60)
    print("TESTING ORCHESTRATOR — FULL PIPELINE")
    print("=" * 60)
    print()

    pipeline = MedResearchPipeline()

    question = "What are the side effects of metformin?"
    result = await pipeline.run(question, verbose=True)

    # Display final result
    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print()
    print(f"  Question:      {result.question}")
    print(f"  Status:        {result.status}")
    print(f"  Confidence:    {result.confidence:.2f}")
    print(f"  Answer length: {len(result.answer)} chars")
    print(f"  Claims:        {len(result.claims)}")
    print(f"  Sources:       {len(result.sources)}")
    print(f"  Total time:    {result.total_duration_ms}ms")
    print()
    print("-" * 60)
    print("STAGE TIMINGS")
    print("-" * 60)
    for stage, ms in result.stage_timings.items():
        print(f"  {stage:20s} {ms:>6d}ms")
    print()
    print("-" * 60)
    print("ANSWER PREVIEW")
    print("-" * 60)
    print()
    print(result.answer[:500] + ("..." if len(result.answer) > 500 else ""))
    print()
    print("-" * 60)
    print("VERIFICATION SUMMARY")
    print("-" * 60)
    if result.verification:
        print(f"  Verified:      {result.verification.verified_count}/{result.verification.total_claims}")
        print(f"  Rate:          {result.verification.verification_rate:.0%}")
        print(f"  Verdict:       {result.verification.verdict}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())