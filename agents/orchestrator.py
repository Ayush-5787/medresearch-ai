"""
MedResearch AI — Orchestrator (v1.1: English-only input policy)
Coordinates the full 6-agent pipeline into one clean interface.

History (report-ready):
- v0 attempted translate-then-retrieve for 60+ languages. Evaluation showed
  non-English answers could not be verified against English-language sources
  (verification of a translation is not verification of a claim).
- v1 refuses non-English input at the guard — <1s, zero tokens, graceful
  bilingual message. Translation machinery is retained but unreachable,
  scheduled for re-evaluation in v2.
- v1 treats Verifier ERROR verdicts as NEUTRAL: infrastructure failures
  must not count as logic failures in status or confidence.
- v1.1: skips verification when the Writer fails (no answer = nothing to
  verify; saves ~10 LLM calls per failed case). Adds a coverage guard:
  a PASS computed from a mostly-errored verification sample is downgraded
  to neutral ERROR — a PASS from 4/10 claims is not evidence.
"""

import time
from typing import Optional
from agents.search_agent import SearchAgent
from agents.reader_agent import ReaderAgent
from agents.writer_agent import WriterAgent
from agents.critic_agent import CriticAgent
from agents.revision_agent import RevisionAgent
from agents.verifier_agent import VerifierAgent
from core.schemas import ResearchAnswer, FinalResult, VerificationReport
from core.language import LanguageHandler
from core.country import CountryConfig
from core.language_guard import language_guard, REFUSAL_UNSUPPORTED_LANGUAGE


class MedResearchPipeline:
    """
    The complete MedResearch AI pipeline.
    v1: English-only input, enforced at the guard.
    """

    def __init__(self):
        # Agents
        self.search_agent = SearchAgent()
        self.reader_agent = ReaderAgent()
        self.writer_agent = WriterAgent()
        self.critic_agent = CriticAgent()
        self.revision_agent = RevisionAgent()
        self.verifier_agent = VerifierAgent()

        # Multi-language support (detection reused by guard; translation
        # machinery retained but unreachable under v1 policy)
        self.language = LanguageHandler()
        self.country = CountryConfig()

    async def run(
        self,
        question: str,
        language: str = "auto",
        country: str = "DEFAULT",
        verbose: bool = True,
    ) -> FinalResult:
        """
        Run the full pipeline on a question.

        Args:
            question: User question (v1: English only — non-English refused)
            language: 'auto' for auto-detect, or ISO code like 'hi', 'en'
            country: ISO country code like 'IN', 'US'
            verbose: Print progress logs
        """
        start_time = time.time()
        stage_timings = {}

        def log(msg: str):
            if verbose:
                print(msg)

        log("=" * 60)
        log("MEDRESEARCH PIPELINE START")
        log("=" * 60)

        # ---------- INPUT GUARD (v1) ----------
        # English-only policy. Refuses in <1s with zero LLM calls.
        ok, reason = language_guard(question)
        if not ok:
            return self._refuse(question, reason, start_time, stage_timings, verbose)

        # ---------- LANGUAGE DETECTION ----------
        log("\n[Language] Detecting...")
        t = time.time()
        detected_lang = (
            self.language.detect_language(question)
            if language == "auto"
            else language
        )
        stage_timings["language_detect_ms"] = int((time.time() - t) * 1000)

        lang_name = self.language.get_language_name(detected_lang)
        log(f"[Language] Detected: {lang_name} ({detected_lang})")

        # ---------- TRANSLATE TO ENGLISH ----------
        # Unreachable under v1 (guard refuses non-English first).
        # Retained for v2 re-evaluation of translate-then-retrieve.
        english_question = question
        if detected_lang != "en":
            log(f"\n[Translation] {lang_name} → English...")
            t = time.time()
            english_question = self.language.translate_to_english(question, detected_lang)
            stage_timings["translate_to_en_ms"] = int((time.time() - t) * 1000)
            log(f"[Translation] → {english_question}")

        log(f"\nQuestion: {english_question}")

        # ---------- COUNTRY CONFIG ----------
        country_info = self.country.get(country)
        emergency = country_info.get("emergency", "112")
        log(f"[Country] {country_info.get('name', country)} — emergency: {emergency}")

        # ---------- STAGE 1: SEARCH ----------
        log("\nSTAGE 1: Search")
        log("-" * 60)
        t = time.time()
        search_result = await self.search_agent.run(english_question)
        stage_timings["search_ms"] = int((time.time() - t) * 1000)
        log(f"Found {len(search_result.sources)} sources "
            f"({search_result.pubmed_count} PubMed, {search_result.web_count} web)\n")

        # ---------- STAGE 2: READ ----------
        log("STAGE 2: Read")
        log("-" * 60)
        t = time.time()
        claims = await self.reader_agent.run(search_result)
        stage_timings["reader_ms"] = int((time.time() - t) * 1000)
        log(f"Extracted {len(claims)} claims\n")

        # Degradation signal: sources fetched but nothing survived extraction.
        # Distinguishes infra/model failure from logic failure downstream.
        extraction_degraded = getattr(self.reader_agent, "extraction_degraded", False)
        if extraction_degraded:
            log("⚠️ [Pipeline] Extraction degraded — sources fetched but 0 claims extracted")

        # ---------- STAGE 3: WRITE ----------
        log("STAGE 3: Write")
        log("-" * 60)
        t = time.time()
        answer = await self.writer_agent.run(english_question, claims)
        stage_timings["writer_ms"] = int((time.time() - t) * 1000)
        log(f"Drafted {len(answer.answer)} chars (confidence={answer.confidence:.2f})\n")

        # ---------- STAGE 4: CRITIQUE ----------
        log("STAGE 4: Critique")
        log("-" * 60)
        t = time.time()
        critique = await self.critic_agent.run(answer, original_claims=claims)
        stage_timings["critic_ms"] = int((time.time() - t) * 1000)
        log(f"Status: {critique.status}, Score: {critique.overall_score:.2f}, "
            f"Issues: {len(critique.issues)}\n")

        # ---------- STAGE 5: REVISE ----------
        log("STAGE 5: Revise")
        log("-" * 60)
        t = time.time()
        revised, rev_metadata = await self.revision_agent.run(
            answer, critique, original_claims=claims
        )
        stage_timings["revision_ms"] = int((time.time() - t) * 1000)
        log(f"Delta: {rev_metadata.get('delta', 0):.2f}, "
            f"Patches: {rev_metadata.get('patches_applied', 0)}\n")

        # ---------- STAGE 6: VERIFY ----------
        log("STAGE 6: Verify")
        log("-" * 60)
        t = time.time()
        if not revised.answer.strip():
            # Writer failed upstream — nothing to verify. Skipping saves
            # ~10 LLM calls per failed case and protects eval quota.
            log("Skipped — no answer to verify (Writer failed)")
            verification = VerificationReport(
                total_claims=0,
                verdict="ERROR",
                error_count=len(revised.claims),
                reasoning="Verification skipped — Writer produced no answer (upstream LLM failure).",
            )
        else:
            verification = await self.verifier_agent.run(revised)
            # Coverage guard: a PASS computed from a mostly-errored sample is
            # not evidence. If more than half the claims errored, downgrade
            # PASS to neutral ERROR so the final status lands on REVIEW.
            if (
                verification.verdict == "PASS"
                and verification.total_claims > 0
                and verification.error_count > verification.total_claims / 2
            ):
                log(f"⚠️ Coverage guard: {verification.error_count}/{verification.total_claims} "
                    f"claims errored — PASS sample too small, downgraded to ERROR (neutral)")
                verification.verdict = "ERROR"
        stage_timings["verifier_ms"] = int((time.time() - t) * 1000)
        err_count = getattr(verification, "error_count", 0)
        err_note = f", {err_count} errored (excluded)" if err_count else ""
        log(f"Verification: {verification.verified_count}/{verification.total_claims} "
            f"({verification.verification_rate:.0%}) — {verification.verdict}{err_note}\n")

        # ---------- TRANSLATE BACK ----------
        # Unreachable under v1 (guard refuses non-English first).
        final_answer_text = revised.answer
        if detected_lang != "en":
            log(f"\n[Translation] English → {lang_name}...")
            t = time.time()
            final_answer_text = self.language.translate_from_english(
                revised.answer, detected_lang
            )
            stage_timings["translate_from_en_ms"] = int((time.time() - t) * 1000)
            log(f"[Translation] Done ({len(final_answer_text)} chars)")

        # ---------- BUILD FINAL RESULT ----------
        total_ms = int((time.time() - start_time) * 1000)

        # Verifier ERROR = infrastructure, not logic. Confidence must not be
        # punished by a 0.0 rate from failed verification calls.
        if verification.verdict == "ERROR":
            final_confidence = (
                0.6 * critique.overall_score + 0.4 * revised.confidence
            )
        else:
            final_confidence = (
                0.4 * critique.overall_score
                + 0.4 * verification.verification_rate
                + 0.2 * revised.confidence
            )

        if critique.status == "BLOCK" or verification.verdict == "FAIL":
            final_status = "BLOCKED"
            final_reasoning = "Failed critique or verification."
        elif verification.verdict == "ERROR":
            # Neutral: unverified ≠ failed. Flag for review, don't block.
            final_status = "REVIEW"
            final_reasoning = (
                "Verification could not run (infrastructure error) — "
                "answer unverified, not failed."
            )
        elif critique.status == "PASS" and verification.verdict == "PASS":
            final_status = "PASS"
            final_reasoning = "Passed all checks and verification."
        else:
            final_status = "REVIEW"
            final_reasoning = "Passed with minor concerns; review recommended."

        if extraction_degraded:
            final_reasoning += " [extraction_degraded]"

        log("\n" + "=" * 60)
        log("PIPELINE COMPLETE")
        log("=" * 60)
        log(f"  Language:       {lang_name}")
        log(f"  Country:        {country_info.get('name', country)}")
        log(f"  Total time:     {total_ms}ms")
        log(f"  Final status:   {final_status}")
        log(f"  Final confidence: {final_confidence:.2f}")
        log(f"  Verified:       {verification.verified_count}/{verification.total_claims}")
        if err_count:
            log(f"  Verify errors:  {err_count} (infrastructure — excluded)")
        log(f"  Emergency:      {emergency}")
        log("=" * 60)

        return FinalResult(
            question=question,
            answer=final_answer_text,
            claims=revised.claims,
            sources=revised.sources,
            critique=critique,
            verification=verification,
            confidence=round(final_confidence, 3),
            status=final_status,
            reasoning=final_reasoning,
            disclaimer=revised.disclaimer,
            agent_trace=revised.agent_trace,
            total_duration_ms=total_ms,
            stage_timings=stage_timings,
        )

    # ----------------------------------------------------------
    # GUARD REFUSAL
    # ----------------------------------------------------------

    def _refuse(
        self,
        question: str,
        reason: str,
        start_time: float,
        stage_timings: dict,
        verbose: bool = True,
    ) -> FinalResult:
        """Build a refusal result without running any agent.

        Zero LLM calls, <1s. The reason code goes in `reasoning` so the
        eval harness can match it against expected_refusal_reason.
        """
        total_ms = int((time.time() - start_time) * 1000)

        messages = {
            REFUSAL_UNSUPPORTED_LANGUAGE: (
                "I'm sorry — this system currently answers questions in English only. "
                "वर्तमान में यह सिस्टम केवल अंग्रेज़ी में प्रश्नों के उत्तर देता है। "
                "Actualmente, este sistema responde preguntas solo en inglés."
            ),
        }
        answer_text = messages.get(reason, f"Request refused: {reason}.")

        if verbose:
            print(f"[Pipeline] ⛔ REFUSAL ({reason}) in {total_ms}ms — no agents run")

        return FinalResult(
            question=question,
            answer=answer_text,
            claims=[],
            sources=[],
            critique=self._empty_critique(),
            verification=VerificationReport(
                total_claims=0,
                verdict="PASS",
                reasoning="Verification not run — input refused at guard.",
            ),
            confidence=0.0,
            status="BLOCKED",
            reasoning=reason,
            disclaimer=(
                "This system provides research information, not medical advice. "
                "Consult a qualified clinician."
            ),
            agent_trace=[],
            total_duration_ms=total_ms,
            stage_timings=stage_timings,
        )

    def _empty_critique(self):
        """Minimal BLOCK critique for guard refusals (no LLM calls).

        Class name resolved defensively — if construction fails, returns None
        (works if FinalResult.critique is Optional).
        """
        import core.schemas as schemas
        for name in ("CritiqueResult", "Critique", "CritiqueReport"):
            cls = getattr(schemas, name, None)
            if cls is None:
                continue
            try:
                return cls(status="BLOCK", overall_score=0.0, issues=[])
            except Exception:
                continue
        return None


print("[orchestrator] MedResearchPipeline loaded (v1.1: English-only + coverage guard)")