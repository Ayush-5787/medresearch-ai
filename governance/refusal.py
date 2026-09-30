"""
MedResearch AI — Refusal Mechanism
Generates clear, helpful refusal messages when answers can't be trusted.

This is the "blockable" pillar of MedResearch AI — safe failure mode.
"""

from typing import List
from core.schemas import (
    AuditReport,
    RefusalMessage,
    FinalResult,
)


TRUSTED_SOURCES = [
    {
        "name": "PubMed (NIH)",
        "url": "https://pubmed.ncbi.nlm.nih.gov/",
        "why": "Peer-reviewed medical literature",
    },
    {
        "name": "WHO",
        "url": "https://www.who.int/",
        "why": "World Health Organization guidelines",
    },
    {
        "name": "Mayo Clinic",
        "url": "https://www.mayoclinic.org/",
        "why": "Patient-friendly medical information",
    },
    {
        "name": "CDC",
        "url": "https://www.cdc.gov/",
        "why": "US Centers for Disease Control",
    },
]


class RefusalBuilder:
    """
    Builds clear refusal messages from audit reports.
    """

    EMERGENCY_NOTE = (
        "If this is a medical emergency, call 108 (India) or your local "
        "emergency number immediately."
    )

    def build(
        self,
        result: FinalResult,
        audit_report: AuditReport,
    ) -> RefusalMessage:
        """Build a refusal message from an audit report."""

        # If PASS → no refusal needed
        if audit_report.decision == "PASS":
            return RefusalMessage(
                title="Answer approved",
                reason="All governance rules passed.",
                level="NONE",
                original_question=result.question,
            )

        # Determine level
        level = "SOFT" if audit_report.decision == "BLOCKED" else "HARD"

        # Extract failed rules
        failed_rules = [
            f"{r.rule_id}: {r.name}"
            for r in audit_report.rules
            if not r.passed
        ]

        # Build reason
        reason = self._build_reason(audit_report, failed_rules)

        # Build details
        details = self._build_details(audit_report, result)

        # Build next steps
        next_steps = self._build_next_steps(level, failed_rules)

        # Build title based on level
        title = (
            "I cannot fully verify this answer"
            if level == "SOFT"
            else "I cannot answer this safely"
        )

        return RefusalMessage(
            title=title,
            reason=reason,
            details=details,
            level=level,
            next_steps=next_steps,
            trusted_sources=TRUSTED_SOURCES,
            emergency_note=self.EMERGENCY_NOTE,
            failed_rules=failed_rules,
            original_question=result.question,
        )

    def _build_reason(self, audit: AuditReport, failed_rules: List[str]) -> str:
        """Build a short reason line."""
        if audit.critical_failures > 0:
            return (
                f"{len(failed_rules)} rule(s) failed "
                f"(including {audit.critical_failures} critical)."
            )
        return f"{len(failed_rules)} governance rule(s) failed."

    def _build_details(self, audit: AuditReport, result: FinalResult) -> str:
        """Build detailed explanation."""
        lines = []

        # Per-rule details
        for r in audit.rules:
            if not r.passed:
                lines.append(f"• {r.name}: {r.actual_value} (need {r.threshold})")

        # Add context
        if result.verification:
            lines.append(
                f"• Verification: {result.verification.verified_count}/"
                f"{result.verification.total_claims} claims verified "
                f"({result.verification.verification_rate:.0%})."
            )

        return " ".join(lines)

    def _build_next_steps(self, level: str, failed_rules: List[str]) -> List[str]:
        """Suggest next steps based on failure type."""
        steps = []

        # Generic suggestions
        steps.append("Try rephrasing your question with more specific terms.")

        # If unsafe language detected
        if any("unsafe" in r.lower() for r in failed_rules):
            steps.append(
                "The answer contained language that could be mistaken for "
                "medical advice. Consult a licensed doctor for personal advice."
            )

        # If verification failed
        if any("verification" in r.lower() for r in failed_rules):
            steps.append(
                "Not all claims could be verified against trusted sources. "
                "This can happen for very recent or niche topics."
            )

        # If confidence low
        if any("confidence" in r.lower() for r in failed_rules):
            steps.append(
                "The overall confidence was below our safety threshold. "
                "Consider asking a more focused question."
            )

        # Standard final step
        steps.append("Consult a licensed doctor for personal medical advice.")

        return steps


print("[refusal] RefusalBuilder loaded")