"""
MedResearch AI — Test Refusal Mechanism
Tests refusal messages for different failure scenarios.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.orchestrator import MedResearchPipeline
from governance.audit_gate import AuditGate
from governance.refusal import RefusalBuilder


def print_refusal(refusal, title: str):
    """Pretty-print a refusal message."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)
    print()
    print(f"  Title:      {refusal.title}")
    print(f"  Level:      {refusal.level}")
    print(f"  Reason:     {refusal.reason}")
    print(f"  Details:    {refusal.details}")
    print()
    if refusal.failed_rules:
        print("  Failed rules:")
        for r in refusal.failed_rules:
            print(f"    • {r}")
    print()
    if refusal.next_steps:
        print("  Next steps:")
        for i, s in enumerate(refusal.next_steps, 1):
            print(f"    {i}. {s}")
    print()
    if refusal.trusted_sources:
        print("  Trusted sources:")
        for s in refusal.trusted_sources:
            print(f"    • {s['name']}: {s['url']}")
    print()
    print(f"  Emergency:  {refusal.emergency_note}")
    print()


async def main():
    print("=" * 60)
    print("TESTING REFUSAL MECHANISM")
    print("=" * 60)

    audit_gate = AuditGate()
    refusal_builder = RefusalBuilder()

    # ==========================================================
    # TEST 1: Real answer → PASS → no refusal
    # ==========================================================
    print("\n\n" + "=" * 60)
    print("TEST 1: REAL ANSWER (expect PASS)")
    print("=" * 60)

    pipeline = MedResearchPipeline()
    result = await pipeline.run("What are the side effects of metformin?", verbose=False)

    audit1 = audit_gate.evaluate(result)
    print(f"\nAudit decision: {audit1.decision}")

    if audit1.decision == "PASS":
        print("  → No refusal needed. Answer is safe to display.")
    else:
        refusal1 = refusal_builder.build(result, audit1)
        print_refusal(refusal1, "REFUSAL MESSAGE")

    # ==========================================================
    # TEST 2: Tampered answer → BLOCKED or REFUSED
    # ==========================================================
    print("\n\n" + "=" * 60)
    print("TEST 2: TAMPERED ANSWER (expect BLOCK/REFUSE)")
    print("=" * 60)
    print()
    print("Tampering answer with unsafe language...")

    # Tamper
    result.answer = (
        "You should take metformin to cure diabetes. "
        "I prescribe it for all my patients. "
        "Take this medicine daily."
    )
    result.confidence = 0.35  # Low confidence

    audit2 = audit_gate.evaluate(result)
    print(f"\nAudit decision: {audit2.decision}")

    refusal2 = refusal_builder.build(result, audit2)
    print_refusal(refusal2, "REFUSAL MESSAGE — TAMPERED")

    # ==========================================================
    # Summary
    # ==========================================================
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"\n  Test 1 (real answer):     {audit1.decision}")
    print(f"  Test 2 (tampered answer): {audit2.decision}")
    print(f"\n  Refusal 2 level: {refusal2.level}")
    print(f"  Refusal 2 has {len(refusal2.next_steps)} next steps")
    print(f"  Refusal 2 has {len(refusal2.trusted_sources)} trusted sources")
    print()


if __name__ == "__main__":
    asyncio.run(main())