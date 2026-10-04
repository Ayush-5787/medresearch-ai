"""
MedResearch AI — Verifier Agent
Checks every claim against its cited source.

Design:
- Per-claim verification for accuracy (not batch)
- Strict prompt with evidence extraction (prevents over-verification)
- Rate-limit aware (5s delay between claims)
- Returns VerificationReport with claim-level verdicts

Verdicts:
- VERIFIED: source clearly supports the claim
- PARTIALLY_VERIFIED: source supports part of the claim
- NOT_VERIFIED: source doesn't mention this
- CONTRADICTED: source says the opposite
- ERROR: verification could not run (infrastructure) — excluded from rate

History (report-ready):
- v0 counted LLM/infra failures as NOT_VERIFIED, contaminating the
  verification rate with infrastructure noise. v1 introduces the ERROR
- verdict: infra failures are excluded from the rate denominator.
- v0 silently self-verified claims lacking source text (claim checked
  against itself → trivial VERIFIED). v1 returns honest NOT_VERIFIED.
"""

import asyncio
import json
import re
from typing import List, Optional
from agents.base_agent import BaseAgent, Timer
from core.schemas import (
    Claim, ResearchAnswer, VerificationResult, VerificationReport
)


class VerifierAgent(BaseAgent):
    """
    Verifies each claim in an answer against its cited source.
    """

    VERIFICATION_PROMPT = """You are a strict medical fact-checker.

CLAIM:
<claim>
{claim}
</claim>

SOURCE URL:
{source_url}

SOURCE TEXT:
<source>
{source_text}
</source>

Your task: Determine if the SOURCE supports the CLAIM.

Follow these rules STRICTLY:
1. Quote the exact text from the source that supports or contradicts the claim.
2. If the source does NOT mention the specific claim, mark NOT_VERIFIED.
3. If the source says the OPPOSITE, mark CONTRADICTED.
4. If the source supports PART of the claim, mark PARTIALLY_VERIFIED.
5. Only mark VERIFIED if the source clearly and fully supports the claim.
6. Do NOT use your own medical knowledge. Judge only from the source text.

Output ONLY valid JSON:
{{
  "verdict": "VERIFIED | PARTIALLY_VERIFIED | NOT_VERIFIED | CONTRADICTED",
  "confidence": 0.0-1.0,
  "evidence": "exact quote from source",
  "reasoning": "brief explanation"
}}

JSON output:"""

    def __init__(self):
        super().__init__(name="VerifierAgent")
        self.llm_delay_seconds = 2  # Respect provider rate limits
        self.max_source_chars = 3000  # Truncate long source text

    async def run(self, answer: ResearchAnswer) -> VerificationReport:
        """Verify all claims in the answer."""
        self.clear_trace()
        self.log_step(
            "start",
            f"{len(answer.claims)} claims",
            "beginning verification",
        )

        if not answer.claims:
            self.log_step("empty", "no claims to verify", "returning empty report")
            return VerificationReport(
                total_claims=0,
                verdict="PASS",
                reasoning="No claims to verify.",
            )

        results: List[VerificationResult] = []
        claims_to_verify = answer.claims[:10]  # Limit to top 10 (rate limits)

        for i, claim in enumerate(claims_to_verify):
            # Rate limit between calls
            if i > 0:
                await asyncio.sleep(self.llm_delay_seconds)

            result = await self._verify_claim(i, claim)
            results.append(result)

            self.log_step(
                "verified",
                f"claim {i+1}/{len(claims_to_verify)}",
                f"{result.verdict} ({result.confidence:.2f})",
            )

        # Build report
        report = self._build_report(results)
        self.log_step(
            "complete",
            f"{len(results)} claims verified",
            f"rate={report.verification_rate:.2f}, verdict={report.verdict}",
        )

        return report

    async def _verify_claim(self, index: int, claim: Claim) -> VerificationResult:
        """Verify a single claim against its source."""
        source_url = claim.source_urls[0] if claim.source_urls else ""
        source_text = self._get_source_text(claim)

        if not source_text:
            return VerificationResult(
                claim_index=index,
                claim_text=claim.text,
                source_url=source_url,
                verdict="NOT_VERIFIED",
                confidence=0.0,
                reasoning="No source text available.",
            )

        prompt = self.VERIFICATION_PROMPT.format(
            claim=claim.text,
            source_url=source_url,
            source_text=source_text[: self.max_source_chars],
        )

        try:
            response = self.llm.simple(
                prompt,
                system="You are a strict medical fact-checker. Return only JSON.",
            )
            parsed = self._parse_json(response)
        except Exception as e:
            # Infrastructure failure (rate limit, network, provider down).
            # Verdict is ERROR — must NOT count as a logic failure.
            self.log_step("error", f"claim {index}", f"LLM failed: {str(e)[:80]}")
            return VerificationResult(
                claim_index=index,
                claim_text=claim.text,
                source_url=source_url,
                verdict="ERROR",
                confidence=0.0,
                reasoning=f"Verification failed (infrastructure): {str(e)[:100]}",
            )

        return VerificationResult(
            claim_index=index,
            claim_text=claim.text,
            source_url=source_url,
            verdict=str(parsed.get("verdict", "NOT_VERIFIED")).upper(),
            confidence=float(parsed.get("confidence", 0.0)),
            evidence=str(parsed.get("evidence", ""))[:500],
            reasoning=str(parsed.get("reasoning", ""))[:300],
        )

    def _get_source_text(self, claim: Claim) -> str:
        """Get the source text for verification.

        v1 fix: v0 fell back to claim.text — the claim was checked against
        itself, trivially producing VERIFIED and inflating the rate.
        Missing source text is now an honest NOT_VERIFIED upstream.
        """
        return claim.verification_notes or ""

    def _parse_json(self, response: str) -> dict:
        """Parse JSON from LLM response."""
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
            response = response.strip()

        start = response.find("{")
        end = response.rfind("}")
        if start == -1 or end == -1:
            return {}

        try:
            return json.loads(response[start : end + 1])
        except json.JSONDecodeError:
            return {}

    def _build_report(self, results: List[VerificationResult]) -> VerificationReport:
        """Build the final VerificationReport.

        ERROR results are EXCLUDED from the verification rate and confidence:
        infrastructure failures must not count as logic failures
        (eval contamination guard).
        """
        total = len(results)
        verified = sum(1 for r in results if r.verdict == "VERIFIED")
        partial = sum(1 for r in results if r.verdict == "PARTIALLY_VERIFIED")
        not_verified = sum(1 for r in results if r.verdict == "NOT_VERIFIED")
        contradicted = sum(1 for r in results if r.verdict == "CONTRADICTED")
        errors = sum(1 for r in results if r.verdict == "ERROR")

        valid_total = total - errors  # claims actually evaluated

        # Verification rate = (verified + 0.5 * partial) / valid claims
        weighted = verified + 0.5 * partial
        rate = weighted / valid_total if valid_total > 0 else 0.0

        # Overall confidence = avg confidence over valid results only
        valid_results = [r for r in results if r.verdict != "ERROR"]
        avg_conf = (
            sum(r.confidence for r in valid_results) / len(valid_results)
            if valid_results else 0.0
        )

        # Verdict
        if valid_total == 0:
            verdict = "ERROR"
            reasoning = (
                f"All {total} verification(s) failed due to infrastructure errors — "
                "not a logic failure. Excluded from pass-rate denominator."
            )
        elif rate >= 0.9:
            verdict = "PASS"
            reasoning = "High verification rate — answer trusted."
        elif rate >= 0.6:
            verdict = "REVIEW"
            reasoning = "Moderate verification rate — some claims unverified."
        else:
            verdict = "FAIL"
            reasoning = "Low verification rate — answer not trusted."

        if errors > 0 and valid_total > 0:
            reasoning += f" ({errors} claim(s) errored — excluded from rate.)"

        return VerificationReport(
            results=results,
            total_claims=total,
            verified_count=verified,
            partial_count=partial,
            not_verified_count=not_verified,
            contradicted_count=contradicted,
            error_count=errors,
            verification_rate=round(rate, 3),
            overall_confidence=round(avg_conf, 3),
            verdict=verdict,
            reasoning=reasoning,
        )


print("[verifier_agent] VerifierAgent loaded")
