"""
MedResearch AI — Test Revision Agent
Tests the Revision Agent in two scenarios:
1. Clean path — Critic finds 0 issues, Revision returns unchanged
2. Dirty path — artificially inject a bad answer, Revision fixes it
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.search_agent import SearchAgent
from agents.reader_agent import ReaderAgent
from agents.writer_agent import WriterAgent
from agents.critic_agent import CriticAgent
from agents.revision_agent import RevisionAgent
from core.schemas import ResearchAnswer, Critique, Issue, Claim


async def test_clean_path():
    """Full pipeline: Search → Read → Write → Critique → Revise."""
    print("\n" + "=" * 60)
    print("TEST 1: CLEAN PATH (full pipeline)")
    print("=" * 60 + "\n")

    question = "What are the side effects of metformin?"

    print("STAGE 1: Search")
    print("-" * 60)
    search_agent = SearchAgent()
    search_result = await search_agent.run(question)
    print(f"Found {len(search_result.sources)} sources\n")

    print("STAGE 2: Read")
    print("-" * 60)
    reader_agent = ReaderAgent()
    claims = await reader_agent.run(search_result)
    print(f"Extracted {len(claims)} claims\n")

    print("STAGE 3: Write")
    print("-" * 60)
    writer_agent = WriterAgent()
    answer = await writer_agent.run(question, claims)
    print(f"Drafted {len(answer.answer)} chars\n")

    print("STAGE 4: Critique")
    print("-" * 60)
    critic_agent = CriticAgent()
    critique = await critic_agent.run(answer, original_claims=claims)
    print(f"Status: {critique.status}, Score: {critique.overall_score:.2f}\n")

    print("STAGE 5: Revision")
    print("-" * 60)
    revision_agent = RevisionAgent()
    revised, metadata = await revision_agent.run(answer, critique, original_claims=claims)

    print("\n  Revision metadata:")
    for k, v in metadata.items():
        print(f"    {k}: {v}")

    print(f"\n  Final status: {revised.status}")
    print(f"  Answer length: {len(revised.answer)} chars")


async def test_dirty_path():
    """Inject a bad answer with issues, verify Revision Agent fixes them."""
    print("\n" + "=" * 60)
    print("TEST 2: DIRTY PATH (injected issues)")
    print("=" * 60 + "\n")

    bad_answer = ResearchAnswer(
        question="What are the side effects of metformin?",
        answer=(
            "You should take metformin to cure diabetes. "
            "It definitely causes weight loss and helps with everything. "
            "Metformin was approved by the FDA in 1994. "
            "Common side effects include nausea and diarrhea [1]. "
            "See your doctor."
        ),
        claims=[
            Claim(
                text="Metformin commonly causes nausea and diarrhea.",
                source_urls=["https://dailymed.nlm.nih.gov/fake1"],
                confidence=0.9,
            ),
            Claim(
                text="Metformin is used to treat type 2 diabetes.",
                source_urls=["https://dailymed.nlm.nih.gov/fake2"],
                confidence=0.95,
            ),
        ],
        confidence=0.5,
        status="PENDING",
    )

    fake_critique = Critique(
        status="REVISE",
        overall_score=0.4,
        issues=[
            Issue(
                type="UNSAFE_ADVICE",
                severity="CRITICAL",
                sentence_index=0,
                description="Answer says 'You should take metformin to cure diabetes' — personalized advice + false cure claim.",
                suggested_fix="Remove prescription language and 'cure' claim. Use neutral phrasing.",
                draft_snippet="You should take metformin to cure diabetes.",
                source_snippet="Metformin is used to treat type 2 diabetes.",
            ),
            Issue(
                type="HALLUCINATION",
                severity="MAJOR",
                sentence_index=1,
                description="'definitely causes weight loss and helps with everything' is not supported by claims.",
                suggested_fix="Delete this sentence or rephrase to match source claims.",
                draft_snippet="It definitely causes weight loss and helps with everything.",
            ),
            Issue(
                type="MISSING_CITATION",
                severity="MAJOR",
                sentence_index=2,
                description="FDA approval date has no citation.",
                suggested_fix="Add citation or delete the sentence.",
                draft_snippet="Metformin was approved by the FDA in 1994.",
            ),
            Issue(
                type="MISSING_DISCLAIMER",
                severity="MINOR",
                description="Answer does not explicitly say 'Consult a licensed doctor.'",
                suggested_fix="Append disclaimer.",
            ),
        ],
        reasoning_summary="Answer contains unsafe advice, hallucination, and missing citation.",
    )

    print("BEFORE REVISION:")
    print("-" * 60)
    print(bad_answer.answer)
    print(f"\n  Critique score: {fake_critique.overall_score}")
    print(f"  Issues: {len(fake_critique.issues)}")

    print("\nREVISING...")
    print("-" * 60)
    revision_agent = RevisionAgent()
    revised, metadata = await revision_agent.run(
        bad_answer, fake_critique, original_claims=bad_answer.claims
    )

    print("\nAFTER REVISION:")
    print("-" * 60)
    print(revised.answer)
    print()
    print("METADATA:")
    for k, v in metadata.items():
        print(f"  {k}: {v}")


async def main():
    await test_clean_path()
    await test_dirty_path()

    print("\n" + "=" * 60)
    print("REVISION AGENT TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())