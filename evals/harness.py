"""
MedResearch AI — Eval harness: runs pipeline against test cases.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Dict, List

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator import MedResearchPipeline
from governance.audit_gate import AuditGate
from evals.metrics import evaluate_checks
from evals.report import build_summary, print_text_report, save_reports


async def run_one(pipeline: MedResearchPipeline, case: Dict[str, Any]) -> Dict[str, Any]:
    """Run a single test case."""
    question = case["question"]
    language = case.get("expected_language", "auto")
    country = case.get("country", "DEFAULT")

    print(f"  ▶ {case['id']}: {question[:60]}...")

    start = time.time()
    try:
        result = await pipeline.run(question, language=language, country=country, verbose=False)
        audit_gate = AuditGate()
        audit_report = audit_gate.evaluate(result)

        eval_result = evaluate_checks(
            result,
            audit_report,
            case.get("checks", []),
            case.get("expected_decision", "PASS"),
        )

        elapsed = round(time.time() - start, 1)
        status = "✅ PASS" if eval_result["passed"] else "❌ FAIL"
        print(f"     {status}  ({elapsed}s)  decision={eval_result['actual_decision']}")

        return {
            "id": case["id"],
            "category": case["category"],
            "question": question,
            "expected_decision": case.get("expected_decision", "PASS"),
            "actual_decision": eval_result["actual_decision"],
            "passed": eval_result["passed"],
            "check_results": eval_result,
            "elapsed_sec": elapsed,
            "error": None,
        }

    except Exception as e:
        elapsed = round(time.time() - start, 1)
        print(f"     ❌ ERROR: {str(e)[:80]}  ({elapsed}s)")
        return {
            "id": case["id"],
            "category": case["category"],
            "question": question,
            "expected_decision": case.get("expected_decision", "PASS"),
            "actual_decision": "ERROR",
            "passed": False,
            "check_results": {"checks": {}, "decision_match": False, "passed": False},
            "elapsed_sec": elapsed,
            "error": str(e)[:200],
        }


async def run_all(cases_path: str = "evals/test_cases.json") -> Dict[str, Any]:
    """Run all test cases."""
    print("═" * 57)
    print("  MEDRESEARCH AI — EVAL HARNESS")
    print("═" * 57)

    data = json.loads(Path(cases_path).read_text(encoding="utf-8"))
    cases = data["test_cases"]
    print(f"  Running {len(cases)} test cases...\n")

    pipeline = MedResearchPipeline()
    results: List[Dict[str, Any]] = []

    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}]", end=" ")
        r = await run_one(pipeline, case)
        results.append(r)

    summary = build_summary(results)
    print()
    print_text_report(summary)

    paths = save_reports(summary)
    print(f"  📄 Text report: {paths['text']}")
    print(f"  📄 JSON report: {paths['json']}")
    print("═" * 57)

    return summary