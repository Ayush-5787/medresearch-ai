"""
MedResearch AI — Test Orchestrator (Multi-Language)
Tests the pipeline with English + Hindi questions.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.orchestrator import MedResearchPipeline


async def main():
    print("=" * 60)
    print("TESTING ORCHESTRATOR — MULTI-LANGUAGE")
    print("=" * 60)

    pipeline = MedResearchPipeline()

    # ==========================================================
    # TEST 1: English question
    # ==========================================================
    print("\n\nTEST 1: ENGLISH QUESTION")
    print("=" * 60)

    result_en = await pipeline.run(
        "What are the side effects of metformin?",
        language="auto",
        country="US",
    )

    print(f"\n[EN Result] Status: {result_en.status}, "
          f"Confidence: {result_en.confidence:.2f}")
    print(f"[EN Answer Preview] {result_en.answer[:200]}...")

    # ==========================================================
    # TEST 2: Hindi question
    # ==========================================================
    print("\n\nTEST 2: HINDI QUESTION")
    print("=" * 60)

    result_hi = await pipeline.run(
        "मेटफॉर्मिन के दुष्प्रभाव क्या हैं?",
        language="auto",
        country="IN",
    )

    print(f"\n[HI Result] Status: {result_hi.status}, "
          f"Confidence: {result_hi.confidence:.2f}")
    print(f"[HI Answer Preview] {result_hi.answer[:300]}...")

    # ==========================================================
    # COMPARISON
    # ==========================================================
    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)
    print(f"\n  English  → status={result_en.status}, "
          f"confidence={result_en.confidence:.2f}, "
          f"verified={result_en.verification.verified_count}/{result_en.verification.total_claims}")
    print(f"  Hindi    → status={result_hi.status}, "
          f"confidence={result_hi.confidence:.2f}, "
          f"verified={result_hi.verification.verified_count}/{result_hi.verification.total_claims}")
    print()


if __name__ == "__main__":
    asyncio.run(main())