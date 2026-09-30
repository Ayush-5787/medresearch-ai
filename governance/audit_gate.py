"""
MedResearch AI — Audit Gate
The governance layer. Enforces deterministic rules before answers reach users.

Rules:
1. All claims must have sources
2. Verification rate ≥ 90%
3. Overall confidence ≥ 0.70
4. No unsafe language
5. Medical disclaimer present
6. Answer has substance (≥ 200 chars)

Decision:
- All pass → PASS
- 1-2 failures → BLOCKED
- 3+ failures or critical → REFUSED
"""

import re
from typing import List
from core.schemas import FinalResult, AuditRule, AuditReport


# Phrases that must NEVER appear (legal compliance)
UNSAFE_PHRASES = [
    "you should take",
    "you must take",
    "i prescribe",
    "take this medicine",
    "stop taking",
    "you have been diagnosed",
    "you are diagnosed",
    "my recommendation",
    "definitely cure",
    "guaranteed cure",
    "will cure",
]


class AuditGate:
    """
    Deterministic governance layer.
    No LLM calls — pure rules for speed and predictability.
    """

    # Thresholds
    MIN_VERIFICATION_RATE = 0.9
    MIN_CONFIDENCE = 0.7
    MIN_ANSWER_LENGTH = 200
    MIN_SOURCES = 1

    def evaluate(self, result: FinalResult) -> AuditReport:
        """Run all governance rules and produce a report."""
        rules: List[AuditRule] = []

        rules.append(self._check_claim_sources(result))
        rules.append(self._check_verification_rate(result))
        rules.append(self._check_confidence(result))
        rules.append(self._check_unsafe_language(result))
        rules.append(self._check_disclaimer(result))
        rules.append(self._check_answer_length(result))

        passed = sum(1 for r in rules if r.passed)
        failed = len(rules) - passed
        critical = sum(1 for r in rules if not r.passed and r.severity == "CRITICAL")

        if failed == 0:
            decision = "PASS"
            reasoning = "All governance rules passed. Answer is compliant."
            safe = True
        elif critical > 0 or failed >= 3:
            decision = "REFUSED"
            reasoning = f"{failed} rules failed (including {critical} critical). Answer not safe to display."
            safe = False
        else:
            decision = "BLOCKED"
            reasoning = f"{failed} rule(s) failed. Answer shown with warnings."
            safe = True

        return AuditReport(
            rules=rules,
            rules_passed=passed,
            rules_failed=failed,
            critical_failures=critical,
            decision=decision,
            reasoning=reasoning,
            safe_to_display=safe,
        )

    # ==========================================================
    # RULE CHECKS
    # ==========================================================

    def _check_claim_sources(self, result: FinalResult) -> AuditRule:
        if not result.claims:
            return AuditRule(
                rule_id="RULE_1",
                name="All claims have sources",
                passed=False,
                actual_value="0 claims",
                threshold="≥ 1 claim with source",
                severity="CRITICAL",
                message="Answer has no claims to verify.",
            )

        without_source = sum(1 for c in result.claims if not c.source_urls)
        passed = without_source == 0

        return AuditRule(
            rule_id="RULE_1",
            name="All claims have sources",
            passed=passed,
            actual_value=f"{len(result.claims) - without_source}/{len(result.claims)} claims sourced",
            threshold="100%",
            severity="CRITICAL",
            message="" if passed else f"{without_source} claims lack sources.",
        )

    def _check_verification_rate(self, result: FinalResult) -> AuditRule:
        if not result.verification:
            return AuditRule(
                rule_id="RULE_2",
                name="Verification rate",
                passed=False,
                actual_value="no verification data",
                threshold=f"≥ {self.MIN_VERIFICATION_RATE:.0%}",
                severity="CRITICAL",
                message="No verification performed.",
            )

        rate = result.verification.verification_rate
        passed = rate >= self.MIN_VERIFICATION_RATE

        return AuditRule(
            rule_id="RULE_2",
            name="Verification rate",
            passed=passed,
            actual_value=f"{rate:.0%}",
            threshold=f"≥ {self.MIN_VERIFICATION_RATE:.0%}",
            severity="CRITICAL",
            message="" if passed else f"Only {rate:.0%} of claims verified.",
        )

    def _check_confidence(self, result: FinalResult) -> AuditRule:
        conf = result.confidence
        passed = conf >= self.MIN_CONFIDENCE

        return AuditRule(
            rule_id="RULE_3",
            name="Overall confidence",
            passed=passed,
            actual_value=f"{conf:.2f}",
            threshold=f"≥ {self.MIN_CONFIDENCE}",
            severity="MAJOR",
            message="" if passed else f"Confidence {conf:.2f} below threshold.",
        )

    def _check_unsafe_language(self, result: FinalResult) -> AuditRule:
        text_lower = result.answer.lower()
        found = [phrase for phrase in UNSAFE_PHRASES if phrase in text_lower]

        passed = len(found) == 0

        return AuditRule(
            rule_id="RULE_4",
            name="No unsafe language",
            passed=passed,
            actual_value=f"{len(found)} violations" if found else "clean",
            threshold="0 violations",
            severity="CRITICAL",
            message="" if passed else f"Found: {', '.join(found[:3])}",
        )

    def _check_disclaimer(self, result: FinalResult) -> AuditRule:
        text_lower = result.answer.lower()
        has_disclaimer = (
            "consult" in text_lower
            and ("doctor" in text_lower or "physician" in text_lower or "medical professional" in text_lower)
        ) or "disclaimer" in text_lower or "for research purposes" in text_lower

        return AuditRule(
            rule_id="RULE_5",
            name="Medical disclaimer present",
            passed=has_disclaimer,
            actual_value="present" if has_disclaimer else "missing",
            threshold="required",
            severity="MAJOR",
            message="" if has_disclaimer else "Answer lacks a medical disclaimer.",
        )

    def _check_answer_length(self, result: FinalResult) -> AuditRule:
        length = len(result.answer)
        passed = length >= self.MIN_ANSWER_LENGTH

        return AuditRule(
            rule_id="RULE_6",
            name="Answer has substance",
            passed=passed,
            actual_value=f"{length} chars",
            threshold=f"≥ {self.MIN_ANSWER_LENGTH} chars",
            severity="MAJOR",
            message="" if passed else f"Answer too short ({length} chars).",
        )


print("[audit_gate] AuditGate loaded")