"""
MedResearch AI — Critic Agent
Reviews a draft answer and finds flaws before it reaches users.

Two-stage design:
  Stage A: Deterministic pre-checks (fast, free, no LLM)
  Stage B: LLM critique (Temp=0, JSON, evidence extraction)
Decision: PASS / REVISE / BLOCK based on decomposed scoring.
"""

import json
import re
from typing import List, Optional
from agents.base_agent import BaseAgent, Timer
from core.schemas import (
    Claim, ResearchAnswer, Critique, Issue, Source
)


# ============================================================
# MEDICAL CONSTITUTION — extensible rule set
# ============================================================

MEDICAL_CONSTITUTION = [
    "Never diagnose a condition.",
    "Never prescribe or recommend specific medicines.",
    "Never give personalized medical advice (no 'you should').",
    "Every sentence must cite at least one source [N].",
    "Prefer peer-reviewed sources over news or blogs.",
    "Use neutral, objective language.",
    "Include a disclaimer directing to a licensed doctor.",
    "If unsure, refuse rather than guess.",
]

# High-risk phrases that should never appear in a medical answer
BLACKLIST_PHRASES = [
    "i prescribe",
    "you must take",
    "you should take",
    "stop taking",
    "definitely cure",
    "guaranteed cure",
    "you have",
    "you are diagnosed",
    "diagnosis is",
    "take this medicine",
    "my recommendation is",
]


class CriticAgent(BaseAgent):
    """
    Reviews a draft answer for issues.
    Returns a Critique with verdict: PASS / REVISE / BLOCK.
    """

    CRITIQUE_PROMPT = """You are a medical auditor. Review the draft answer below.

<question>
{question}
</question>

<claims>
{claims_xml}
</claims>

<draft_answer>
{draft}
</draft_answer>

Your job: find issues in the draft. Check:
1. FAITHFULNESS — Does the draft say anything NOT supported by the claims?
2. CITATIONS — Does every sentence have at least one [N]?
3. SAFETY — Any personalized advice, diagnosis, or prescription? (FORBIDDEN)
4. RELEVANCE — Does the draft answer the question?
5. COMPLETENESS — Any critical claims left out?
6. TONE — Neutral and objective, or prescriptive?

RULES:
- Only flag issues where you can quote BOTH the draft snippet AND the conflicting source.
- Do NOT use your own medical knowledge. Compare ONLY the draft vs the provided claims.
- If the draft is faithful and safe, return an empty issues list.
- Return ONLY valid JSON, no other text.

Output JSON schema:
{{
  "issues": [
    {{
      "type": "HALLUCINATION | MISSING_CITATION | OFF_TOPIC | UNSAFE_ADVICE | INCOMPLETE | TONE",
      "severity": "CRITICAL | MAJOR | MINOR",
      "sentence_index": 0,
      "description": "short explanation",
      "suggested_fix": "how to fix",
      "draft_snippet": "text from draft",
      "source_snippet": "relevant text from source"
    }}
  ],
  "reasoning_summary": "1-2 sentence overall assessment"
}}

JSON output:"""

    def __init__(self):
        super().__init__(name="CriticAgent")
        self.min_citation_ratio = 0.7  # 70% of sentences must have [N]
        self.score_threshold_pass = 0.9
        self.score_threshold_block = 0.6

    async def run(
        self,
        answer: ResearchAnswer,
        original_claims: Optional[List[Claim]] = None,
    ) -> Critique:
        """Review the answer and produce a Critique."""
        self.clear_trace()
        self.log_step(
            "start",
            f"{len(answer.answer)} chars, {len(answer.claims)} claims",
            "beginning critique",
        )

        if not answer.answer:
            self.log_step("empty", "no answer", "returning BLOCK")
            return Critique(
                status="BLOCK",
                overall_score=0.0,
                issues=[Issue(
                    type="EMPTY",
                    severity="CRITICAL",
                    description="Answer is empty.",
                    suggested_fix="Regenerate answer.",
                )],
                reasoning_summary="No content to critique.",
            )

        # Use claims either from answer or passed in
        claims = original_claims or answer.claims

        # STAGE A: Deterministic pre-checks
        with Timer() as t_a:
            pre_issues = self._stage_a_checks(answer, claims)
        self.log_step(
            "stage_a_complete",
            "code-based pre-checks",
            f"{len(pre_issues)} issue(s) found",
            t_a.elapsed_ms,
        )

        # If critical pre-check failures → BLOCK immediately
        critical_pre = [i for i in pre_issues if i.severity == "CRITICAL"]
        if critical_pre:
            return self._build_critique(
                status="BLOCK",
                issues=pre_issues,
                summary=f"Blocked by pre-checks: {critical_pre[0].description}",
                answer=answer,
            )

        # STAGE B: LLM critique
        with Timer() as t_b:
            llm_issues, llm_summary = await self._stage_b_llm_critique(answer, claims)
        self.log_step(
            "stage_b_complete",
            "LLM semantic critique",
            f"{len(llm_issues)} issue(s) found",
            t_b.elapsed_ms,
        )

        # Combine issues
        all_issues = pre_issues + llm_issues

        # Compute score
        score = self._compute_score(all_issues, answer)

        # Decide
        if score < self.score_threshold_block:
            status = "BLOCK"
        elif score < self.score_threshold_pass:
            status = "REVISE"
        else:
            status = "PASS"

        self.log_step(
            "decided",
            f"{len(all_issues)} total issues",
            f"status={status}, score={score:.2f}",
        )

        return self._build_critique(
            status=status,
            issues=all_issues,
            summary=llm_summary or "Critique complete.",
            answer=answer,
            score=score,
        )

    # ----------------------------------------------------------
    # STAGE A: Deterministic checks
    # ----------------------------------------------------------

    def _stage_a_checks(self, answer: ResearchAnswer, claims: List[Claim]) -> List[Issue]:
        """Fast, deterministic checks (no LLM)."""
        issues: List[Issue] = []
        text = answer.answer
        sentences = self._split_sentences(text)

        # Check 1: Citation presence per sentence
        sentences_no_cite = 0
        for i, s in enumerate(sentences):
            if not re.search(r"\[\d+\]", s):
                sentences_no_cite += 1
        if sentences_no_cite > 0 and sentences:
            ratio = 1 - (sentences_no_cite / len(sentences))
            if ratio < self.min_citation_ratio:
                issues.append(Issue(
                    type="MISSING_CITATION",
                    severity="MAJOR",
                    description=f"Only {ratio*100:.0f}% of sentences have citations (need {self.min_citation_ratio*100:.0f}%).",
                    suggested_fix="Ensure every sentence ends with [N].",
                ))

        # Check 2: Citation range
        max_id = len(claims)
        for m in re.finditer(r"\[(\d+)\]", text):
            num = int(m.group(1))
            if num < 1 or num > max_id:
                issues.append(Issue(
                    type="INVALID_CITATION",
                    severity="MAJOR",
                    description=f"Citation [{num}] out of range 1-{max_id}.",
                    suggested_fix="Fix or remove invalid citation.",
                ))
                break  # Only report once

        # Check 3: Blacklist phrases (safety)
        text_lower = text.lower()
        for phrase in BLACKLIST_PHRASES:
            if phrase in text_lower:
                idx = text_lower.find(phrase)
                snippet = text[max(0, idx - 30): idx + 50].strip()
                issues.append(Issue(
                    type="UNSAFE_ADVICE",
                    severity="CRITICAL",
                    description=f"Contains prohibited phrase: '{phrase}'.",
                    suggested_fix="Remove personalized advice / diagnosis language.",
                    draft_snippet=snippet,
                ))

        # Check 4: Length sanity
        if len(text) < 100:
            issues.append(Issue(
                type="TOO_SHORT",
                severity="MAJOR",
                description="Answer is under 100 characters.",
                suggested_fix="Regenerate a fuller answer.",
            ))

        # Check 5: Disclaimer presence
        if "consult" not in text_lower and "doctor" not in text_lower:
            issues.append(Issue(
                type="MISSING_DISCLAIMER",
                severity="MINOR",
                description="Answer does not mention consulting a doctor.",
                suggested_fix="Add 'Consult a licensed doctor...' at the end.",
            ))

        return issues

    # ----------------------------------------------------------
    # STAGE B: LLM critique
    # ----------------------------------------------------------

    async def _stage_b_llm_critique(self, answer: ResearchAnswer, claims: List[Claim]):
        """Semantic critique via LLM. Returns (issues, summary)."""
        claims_xml = self._format_claims(claims)

        prompt = self.CRITIQUE_PROMPT.format(
            question=answer.question,
            claims_xml=claims_xml,
            draft=answer.answer,
        )

        try:
            response = self.llm.simple(
                prompt,
                system="You are a medical auditor. Return only JSON.",
            )
        except Exception as e:
            self.log_step("llm_error", str(e)[:100], "returning empty critique")
            return [], f"LLM critique failed: {str(e)[:100]}"

        parsed = self._parse_json(response)
        raw_issues = parsed.get("issues", [])
        summary = parsed.get("reasoning_summary", "")

        issues = []
        for r in raw_issues:
            if not isinstance(r, dict):
                continue
            try:
                issues.append(Issue(
                    type=str(r.get("type", "OTHER")),
                    severity=str(r.get("severity", "MINOR")).upper(),
                    sentence_index=r.get("sentence_index"),
                    description=str(r.get("description", "")),
                    suggested_fix=str(r.get("suggested_fix", "")),
                    draft_snippet=str(r.get("draft_snippet", "")),
                    source_snippet=str(r.get("source_snippet", "")),
                ))
            except Exception:
                continue

        return issues, summary

    def _format_claims(self, claims: List[Claim]) -> str:
        """Format claims as XML."""
        lines = []
        for i, c in enumerate(claims, 1):
            safe = c.text.replace("<", "&lt;").replace(">", "&gt;")
            url = c.source_urls[0] if c.source_urls else "unknown"
            lines.append(f'<claim id="{i}">')
            lines.append(f'  <text>{safe}</text>')
            lines.append(f'  <source>{url}</source>')
            lines.append(f'</claim>')
        return "\n".join(lines)

    # ----------------------------------------------------------
    # Scoring + Decision
    # ----------------------------------------------------------

    def _compute_score(self, issues: List[Issue], answer: ResearchAnswer) -> float:
        """Decomposed scoring: start at 1.0, subtract per issue."""
        score = 1.0
        for i in issues:
            sev = i.severity.upper()
            if sev == "CRITICAL":
                score -= 0.5
            elif sev == "MAJOR":
                score -= 0.2
            elif sev == "MINOR":
                score -= 0.05
        # Factor in the answer's own confidence
        score = score * 0.7 + answer.confidence * 0.3
        return max(0.0, min(1.0, score))

    def _build_critique(
        self,
        status: str,
        issues: List[Issue],
        summary: str,
        answer: ResearchAnswer,
        score: Optional[float] = None,
    ) -> Critique:
        if score is None:
            score = self._compute_score(issues, answer)
        return Critique(
            status=status,
            overall_score=round(score, 3),
            issues=issues,
            reasoning_summary=summary,
            metrics={
                "n_issues": len(issues),
                "n_critical": sum(1 for i in issues if i.severity.upper() == "CRITICAL"),
                "n_major": sum(1 for i in issues if i.severity.upper() == "MAJOR"),
                "n_minor": sum(1 for i in issues if i.severity.upper() == "MINOR"),
                "answer_confidence": answer.confidence,
            },
        )

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------

    def _split_sentences(self, text: str) -> List[str]:
        """Simple sentence splitter."""
        parts = re.split(r"(?<=[.!?])\s+", text.strip())
        return [p for p in parts if p]

    def _parse_json(self, response: str) -> dict:
        """Extract JSON object from LLM response."""
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
            return json.loads(response[start:end + 1])
        except json.JSONDecodeError:
            return {}


print("[critic_agent] CriticAgent loaded")