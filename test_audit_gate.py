"""
MedResearch AI — Test Audit Gate
Tests governance rules + runs full pipeline + audit.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.orchestrator import MedResearchPipeline
from governance.audit_gate import AuditGate


def print_audit_report(report, title: str):
    """Pretty-print an audit report."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)
    print()
    print(f"  Decision:          {report.decision}")
    print(f"  Safe to display:   {report.safe_to_display}")
    print(f"  Rules passed:      {report.rules_passed}")
    print(f"  Rules failed:      {report.rules_failed}")
    print(f"  Critical failures: {report.critical_failures}")
    print(f"  Reasoning:         {report.reasoning}")
    print()
    print("-" * 60)
    print("RULE-BY-RULE")
    print("-" * 60)
    for r in report.rules:
        icon = "[PASS]" if r.passed else "[FAIL]"
        print(f"\n{icon} {r.rule_id}: {r.name}")
        print(f"   Actual:    {r.actual_value}")
        print(f"   Threshold: {r.threshold}")
        print(f"   Severity:  {r.severity}")
        if r.message:
            print(f"   Message:   {r.message}")
    print()


async def main():
    print("=" * 60)
    print("TESTING AUDIT GATE")
    print("=" * 60)

    audit_gate = AuditGate()

    # ==========================================================
    # TEST 1: Full pipeline (real answer) → expect PASS
    # ==========================================================
    print("\nTEST 1: FULL PIPELINE (real answer)\n")
    pipeline = MedResearchPipeline()

    question = "What are the side effects of metformin?"
    result = await pipeline.run(question, verbose=True)

    report = audit_gate.evaluate(result)
    print_audit_report(report, "AUDIT REPORT — Real Answer")

    # ==========================================================
    # TEST 2: Tampered answer (unsafe language) → expect BLOCK/REFUSE
    # ==========================================================
    print("\n\n" + "=" * 60)
    print("TEST 2: TAMPERED ANSWER (unsafe language)")
    print("=" * 60)
    print()
    print("Modifying real answer to include unsafe phrases...")
    print("  + 'You should take metformin to cure diabetes'")
    print()

    # Tamper the answer
    result.answer = (
        "You should take metformin to cure diabetes. "
        "I prescribe it for all my patients. "
        "Take this medicine daily and stop taking other drugs."
    )
    result.confidence = 0.3

    report2 = audit_gate.evaluate(result)
    print_audit_report(report2, "AUDIT REPORT — Tampered Answer")

    # ==========================================================
    # Summary
    # ==========================================================
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"\n  Test 1 (real answer):     {report.decision}      "
          f"({report.rules_passed}/{len(report.rules)} rules passed)")
    print(f"  Test 2 (tampered answer): {report2.decision}    "
          f"({report2.rules_passed}/{len(report2.rules)} rules passed)")
    print()


if __name__ == "__main__":
    asyncio.run(main())