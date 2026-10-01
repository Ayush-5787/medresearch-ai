"""
MedResearch AI — Orchestrator (with Multi-Language Support)
Coordinates the full 6-agent pipeline into one clean interface.
Supports questions in any language via auto-detection and translation.
"""

import time
from typing import Optional
from agents.search_agent import SearchAgent
from agents.reader_agent import ReaderAgent
from agents.writer_agent import WriterAgent
from agents.critic_agent import CriticAgent
from agents.revision_agent import RevisionAgent
from agents.verifier_agent import VerifierAgent
from core.schemas import ResearchAnswer, FinalResult
from core.language import LanguageHandler
from core.country import CountryConfig


class MedResearchPipeline:
    """
    The complete MedResearch AI pipeline.
    Supports any language via auto-detect + translation.
    """

    def __init__(self):
        # Agents
        self.search_agent = SearchAgent()
        self.reader_agent = ReaderAgent()
        self.writer_agent = WriterAgent()
        self.critic_agent = CriticAgent()
        self.revision_agent = RevisionAgent()
        self.verifier_agent = VerifierAgent()

        # Multi-language support
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
        Run the full pipeline on a question (any language).

        Args:
            question: User question in any language
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
        verification = await self.verifier_agent.run(revised)
        stage_timings["verifier_ms"] = int((time.time() - t) * 1000)
        log(f"Verification: {verification.verified_count}/{verification.total_claims} "
            f"({verification.verification_rate:.0%}) — {verification.verdict}\n")

        # ---------- TRANSLATE BACK ----------
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

        final_confidence = (
            0.4 * critique.overall_score
            + 0.4 * verification.verification_rate
            + 0.2 * revised.confidence
        )

        if critique.status == "BLOCK" or verification.verdict == "FAIL":
            final_status = "BLOCKED"
            final_reasoning = "Failed critique or verification."
        elif critique.status == "PASS" and verification.verdict == "PASS":
            final_status = "PASS"
            final_reasoning = "Passed all checks and verification."
        else:
            final_status = "REVIEW"
            final_reasoning = "Passed with minor concerns; review recommended."

        log("\n" + "=" * 60)
        log("PIPELINE COMPLETE")
        log("=" * 60)
        log(f"  Language:       {lang_name}")
        log(f"  Country:        {country_info.get('name', country)}")
        log(f"  Total time:     {total_ms}ms")
        log(f"  Final status:   {final_status}")
        log(f"  Final confidence: {final_confidence:.2f}")
        log(f"  Verified:       {verification.verified_count}/{verification.total_claims}")
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


print("[orchestrator] MedResearchPipeline loaded (multi-language)")