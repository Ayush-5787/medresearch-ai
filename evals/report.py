"""
MedResearch AI — Eval report generator (text + JSON).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def build_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    by_category: Dict[str, Dict[str, int]] = {}
    for r in results:
        cat = r["category"]
        by_category.setdefault(cat, {"total": 0, "passed": 0})
        by_category[cat]["total"] += 1
        if r["passed"]:
            by_category[cat]["passed"] += 1

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "accuracy": round(100.0 * passed / total, 1) if total else 0.0,
        "by_category": by_category,
        "failed_cases": [r for r in results if not r["passed"]],
        "timestamp": datetime.now().isoformat(),
    }


def print_text_report(summary: Dict[str, Any]) -> None:
    line = "═" * 57
    print(line)
    print("  MEDRESEARCH AI — EVAL REPORT")
    print(f"  Run: {summary['timestamp']}")
    print(line)
    print()
    print(f"  TOTAL:   {summary['passed']}/{summary['total']} passed ({summary['accuracy']}%)")
    print()
    print("  By Category:")
    for cat, stats in summary["by_category"].items():
        pct = round(100.0 * stats["passed"] / stats["total"], 1) if stats["total"] else 0.0
        icon = "✅" if stats["passed"] == stats["total"] else ("⚠️" if stats["passed"] > 0 else "❌")
        print(f"    {icon} {cat:<22} {stats['passed']}/{stats['total']}  ({pct}%)")
    print()

    if summary["failed_cases"]:
        print("  Failed Tests:")
        for r in summary["failed_cases"][:20]:
            print(f"    ❌ {r['id']}: {r['question'][:50]}")
            print(f"       Expected: {r['expected_decision']} | Got: {r['actual_decision']}")
        print()
    else:
        print("  ✅ All tests passed!")
        print()

    print(line)


def save_reports(summary: Dict[str, Any], out_dir: str = "evals_output") -> Dict[str, str]:
    Path(out_dir).mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    txt_path = Path(out_dir) / f"report_{ts}.txt"
    json_path = Path(out_dir) / f"report_{ts}.json"

    # Text
    lines = []
    line = "═" * 57
    lines.append(line)
    lines.append("  MEDRESEARCH AI — EVAL REPORT")
    lines.append(f"  Run: {summary['timestamp']}")
    lines.append(line)
    lines.append("")
    lines.append(f"  TOTAL:   {summary['passed']}/{summary['total']} passed ({summary['accuracy']}%)")
    lines.append("")
    lines.append("  By Category:")
    for cat, stats in summary["by_category"].items():
        pct = round(100.0 * stats["passed"] / stats["total"], 1) if stats["total"] else 0.0
        lines.append(f"    {cat:<22} {stats['passed']}/{stats['total']}  ({pct}%)")
    lines.append("")
    if summary["failed_cases"]:
        lines.append("  Failed Tests:")
        for r in summary["failed_cases"]:
            lines.append(f"    ❌ {r['id']}: {r['question'][:60]}")
            lines.append(f"       Expected: {r['expected_decision']} | Got: {r['actual_decision']}")
            lines.append(f"       Checks:  {r['check_results']['checks']}")
        lines.append("")
    lines.append(line)
    txt_path.write_text("\n".join(lines), encoding="utf-8")

    # JSON
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    return {"text": str(txt_path), "json": str(json_path)}