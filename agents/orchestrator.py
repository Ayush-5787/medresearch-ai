"""
MedResearch AI — Orchestrator
Coordinates the full 6-agent pipeline into one clean interface.

Usage:
    from agents.orchestrator import MedResearchPipeline
    pipeline = MedResearchPipeline()
    result = await pipeline.run("What are the side effects of metformin?")
"""

import time
from typing import Optional
from agents.search_agent import SearchAgent
from agents.reader_agent import ReaderAgent
from agents.writer_agent import WriterAgent
from agents.critic_agent import CriticAgent
from agents.revision_agent import RevisionAgent
from agents.verifier_agent import VerifierAgent
from core.schemas import (
    ResearchAnswer,
    FinalResult,
    VerificationReport,
)


class MedResearchPipeline:
    """
    The complete MedResearch AI pipeline.
    Search → Read → Write → Critique → Revise → Verify.
    """

    def __init__(self):
        self.search_agent = SearchAgent()
        self.reader_agent = ReaderAgent()
        self.writer_agent = WriterAgent()
        self.critic_agent = CriticAgent()
        self.revision_agent = RevisionAgent()
        self.verifier_agent = VerifierAgent()

    async def run(self, question: str, verbose: bool = True) -> FinalResult:
        """Run the full pipeline on a question."""
        start_time = time.time()
        stage_timings = {}

        def log(msg: str):
            if verbose:
                print(msg)

        log("=" * 60)
        log("MEDRESEARCH PIPELINE START")
        log("=" * 60)
        log(f"Question: {question}\n")

        # ---------- STAGE 1: SEARCH ----------
        log("STAGE 1: Search")
        log("-" * 60)
        t = time.time()
        search_result = await self.search_agent.run(question)
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
        answer = await self.writer_agent.run(question, claims)
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

        # ---------- BUILD FINAL RESULT ----------
        total_ms = int((time.time() - start_time) * 1000)

        # Compute final confidence: weight critique + verification
        final_confidence = (
            0.4 * critique.overall_score
            + 0.4 * verification.verification_rate
            + 0.2 * revised.confidence
        )

        # Final status: based on both critique and verification
        if critique.status == "BLOCK" or verification.verdict == "FAIL":
            final_status = "BLOCKED"
            final_reasoning = "Failed critique or verification."
        elif critique.status == "PASS" and verification.verdict == "PASS":
            final_status = "PASS"
            final_reasoning = "Passed all checks and verification."
        else:
            final_status = "REVIEW"
            final_reasoning = "Passed with minor concerns; review recommended."

        log("=" * 60)
        log("PIPELINE COMPLETE")
        log("=" * 60)
        log(f"  Total time:      {total_ms}ms")
        log(f"  Final status:    {final_status}")
        log(f"  Final confidence: {final_confidence:.2f}")
        log(f"  Verified:        {verification.verified_count}/{verification.total_claims}")
        log("=" * 60)

        return FinalResult(
            question=question,
            answer=revised.answer,
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


print("[orchestrator] MedResearchPipeline loaded")