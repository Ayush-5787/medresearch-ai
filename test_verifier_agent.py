"""
MedResearch AI — Test Verifier Agent
Runs the full pipeline + verification.
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
from agents.verifier_agent import VerifierAgent


async def main():
    print("=" * 60)
    print("TESTING FULL PIPELINE WITH VERIFIER")
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
    print(f"Status: {critique.status}, Score: {critique.overall_score:.2f}\n")

    # Stage 5: Revision
    print("STAGE 5: Revision")
    print("-" * 60)
    revision_agent = RevisionAgent()
    revised, rev_metadata = await revision_agent.run(answer, critique, original_claims=claims)
    print(f"Delta: {rev_metadata['delta']:.2f}\n")

    # Stage 6: Verify
    print("STAGE 6: Verify")
    print("-" * 60)
    verifier_agent = VerifierAgent()
    report = await verifier_agent.run(revised)

    # Display verification report
    print("\n" + "=" * 60)
    print("VERIFICATION REPORT")
    print("=" * 60)
    print()
    print(f"  Total claims:      {report.total_claims}")
    print(f"  Verified:          {report.verified_count}")
    print(f"  Partial:           {report.partial_count}")
    print(f"  Not verified:      {report.not_verified_count}")
    print(f"  Contradicted:      {report.contradicted_count}")
    print(f"  Verification rate: {report.verification_rate:.2%}")
    print(f"  Overall verdict:   {report.verdict}")
    print(f"  Reasoning:         {report.reasoning}")
    print()
    print("-" * 60)
    print("CLAIM-BY-CLAIM")
    print("-" * 60)
    for r in report.results:
        icon = {
            "VERIFIED": "[OK]",
            "PARTIALLY_VERIFIED": "[PART]",
            "NOT_VERIFIED": "[NO]",
            "CONTRADICTED": "[X]",
        }.get(r.verdict, "[?]")
        print(f"\n{icon} Claim {r.claim_index + 1}: {r.claim_text[:80]}...")
        print(f"   Verdict:    {r.verdict} ({r.confidence:.2f})")
        print(f"   Source:     {r.source_url[:70]}...")
        if r.evidence:
            print(f"   Evidence:   {r.evidence[:100]}...")
    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())