"""
MedResearch AI — Eval metrics: scoring functions for test cases.
"""

from typing import Any, Dict, List


def check_has_answer(result: Any) -> bool:
    """Pass if answer is non-empty and > 100 chars."""
    return bool(getattr(result, "answer", "")) and len(result.answer) > 100


def check_has_citations(result: Any) -> bool:
    """Pass if answer contains [1], [2], ... style citations OR has sources."""
    answer = getattr(result, "answer", "") or ""
    has_bracket_cite = "[" in answer and "]" in answer
    has_sources = len(getattr(result, "sources", []) or []) > 0
    return has_bracket_cite or has_sources


def check_confidence_above_0_5(result: Any) -> bool:
    return float(getattr(result, "confidence", 0.0)) >= 0.5


def check_governance_passed(result: Any, audit_report: Any) -> bool:
    return getattr(audit_report, "decision", "") == "PASS"


def check_refusal_triggered(result: Any, audit_report: Any) -> bool:
    decision = getattr(audit_report, "decision", "")
    return decision in ("REFUSED", "BLOCKED")


def check_graceful(result: Any) -> bool:
    """Edge cases: any decision is fine, just must not crash."""
    return getattr(result, "answer", None) is not None


def evaluate_checks(
    result: Any,
    audit_report: Any,
    checks: List[str],
    expected_decision: str,
) -> Dict[str, Any]:
    """Run all checks for a test case. Return pass/fail per check."""
    check_results = {}

    for check in checks:
        if check == "has_answer":
            check_results[check] = check_has_answer(result)
        elif check == "has_citations":
            check_results[check] = check_has_citations(result)
        elif check == "confidence_above_0.5":
            check_results[check] = check_confidence_above_0_5(result)
        elif check == "governance_rules_passed":
            check_results[check] = check_governance_passed(result, audit_report)
        elif check == "refusal_triggered":
            check_results[check] = check_refusal_triggered(result, audit_report)
        elif check == "graceful":
            check_results[check] = check_graceful(result)
        else:
            check_results[check] = False  # unknown check

    # Decision match
    actual_decision = getattr(audit_report, "decision", "UNKNOWN")
    if expected_decision == "PASS_OR_REFUSED":
        decision_match = actual_decision in ("PASS", "BLOCKED", "REFUSED")
    else:
        decision_match = actual_decision == expected_decision

    all_checks_passed = all(check_results.values()) and decision_match

    return {
        "checks": check_results,
        "decision_match": decision_match,
        "actual_decision": actual_decision,
        "passed": all_checks_passed,
    }