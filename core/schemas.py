"""
MedResearch AI — Data Schemas
Pydantic models for type-safe data flow between agents.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


# ============================================================
# SOURCE — A piece of evidence from search
# ============================================================

class Source(BaseModel):
    """A single source of medical information."""
    
    url: str = Field(..., description="URL of the source")
    title: str = Field(default="", description="Title of the page/paper")
    snippet: str = Field(default="", description="Relevant text from the source")
    source_type: Literal["pubmed", "web"] = Field(default="web")
    credibility_score: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # PubMed-specific fields (optional)
    pmid: Optional[str] = Field(default=None, description="PubMed ID")
    authors: Optional[List[str]] = Field(default=None)
    year: Optional[str] = Field(default=None)
    journal: Optional[str] = Field(default=None)


# ============================================================
# CLAIM — A single factual statement in an answer
# ============================================================

class Claim(BaseModel):
    """A single claim made in a research answer."""
    
    text: str = Field(..., description="The claim itself")
    source_urls: List[str] = Field(default_factory=list, description="URLs supporting this claim")
    verified: bool = Field(default=False, description="Has this claim been verified?")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    verification_notes: str = Field(default="")


# ============================================================
# AGENT STEP — Log of what an agent did
# ============================================================

class AgentStep(BaseModel):
    """A single action taken by an agent (for explainability)."""
    
    agent_name: str
    action: str
    input_summary: str
    output_summary: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: int = Field(default=0)


# ============================================================
# RESEARCH ANSWER — Final output of the pipeline
# ============================================================

class ResearchAnswer(BaseModel):
    """The final answer produced by the multi-agent pipeline."""
    
    question: str
    answer: str = Field(default="")
    claims: List[Claim] = Field(default_factory=list)
    sources: List[Source] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    status: Literal["PASS", "BLOCKED", "REFUSED", "PENDING"] = Field(default="PENDING")
    reasoning: str = Field(default="")
    agent_trace: List[AgentStep] = Field(default_factory=list)
    disclaimer: str = Field(
        default="This information is for research purposes only. "
                "Always consult a qualified medical professional for medical advice."
    )


# ============================================================
# SEARCH RESULT — Output of the Search Agent
# ============================================================

class SearchResult(BaseModel):
    """Structured output from the Search Agent."""
    
    question: str
    sources: List[Source] = Field(default_factory=list)
    pubmed_count: int = Field(default=0)
    web_count: int = Field(default=0)
    agent_trace: List[AgentStep] = Field(default_factory=list)



# ============================================================
# ISSUE — A single issue found by the Critic
# ============================================================

class Issue(BaseModel):
    """A single issue found by the Critic Agent."""
    
    type: str = Field(..., description="Issue category: HALLUCINATION, MISSING_CITATION, OFF_TOPIC, etc.")
    severity: str = Field(..., description="CRITICAL | MAJOR | MINOR")
    sentence_index: Optional[int] = Field(default=None, description="Which sentence (0-indexed)")
    description: str = Field(..., description="What's wrong")
    suggested_fix: str = Field(default="", description="How to fix it")
    draft_snippet: str = Field(default="", description="Evidence from the draft")
    source_snippet: str = Field(default="", description="Evidence from the source")


# ============================================================
# CRITIQUE — Output of the Critic Agent
# ============================================================

class Critique(BaseModel):
    """Output of the Critic Agent's evaluation."""
    
    status: str = Field(..., description="PASS | REVISE | BLOCK")
    overall_score: float = Field(default=1.0, ge=0.0, le=1.0)
    issues: List[Issue] = Field(default_factory=list)
    reasoning_summary: str = Field(default="")
    metrics: dict = Field(default_factory=dict)


# ============================================================
# VERIFICATION RESULT — Verification of a single claim
# ============================================================

class VerificationResult(BaseModel):
    """Result of verifying one claim against its source."""
    
    claim_index: int = Field(..., description="Index of the claim in the answer")
    claim_text: str = Field(..., description="The claim being verified")
    source_url: str = Field(default="", description="The source URL used")
    verdict: str = Field(..., description="VERIFIED | PARTIALLY_VERIFIED | NOT_VERIFIED | CONTRADICTED")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: str = Field(default="", description="Quote from source supporting the verdict")
    reasoning: str = Field(default="", description="Explanation of the verdict")


# ============================================================
# VERIFICATION REPORT — Full report from the Verifier Agent
# ============================================================

class VerificationReport(BaseModel):
    """Complete verification report for an answer."""
    
    results: List[VerificationResult] = Field(default_factory=list)
    total_claims: int = Field(default=0)
    verified_count: int = Field(default=0)
    partial_count: int = Field(default=0)
    not_verified_count: int = Field(default=0)
    contradicted_count: int = Field(default=0)
    verification_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    verdict: str = Field(default="PENDING", description="PASS | REVIEW | FAIL")
    reasoning: str = Field(default="")


# ============================================================
# FINAL RESULT — Complete output of the full pipeline
# ============================================================

class FinalResult(BaseModel):
    """The complete output of MedResearchPipeline."""
    
    question: str
    answer: str = Field(default="")
    claims: List[Claim] = Field(default_factory=list)
    sources: List[Source] = Field(default_factory=list)
    critique: Optional[Critique] = Field(default=None)
    verification: Optional[VerificationReport] = Field(default=None)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    status: str = Field(default="PENDING")
    reasoning: str = Field(default="")
    disclaimer: str = Field(default="")
    agent_trace: List[AgentStep] = Field(default_factory=list)
    total_duration_ms: int = Field(default=0)
    stage_timings: dict = Field(default_factory=dict)


# ============================================================
# AUDIT RULE — A single governance rule check
# ============================================================

class AuditRule(BaseModel):
    """A single governance rule result."""
    
    rule_id: str = Field(..., description="RULE_1, RULE_2, ...")
    name: str = Field(..., description="Human-readable rule name")
    passed: bool = Field(default=False)
    actual_value: str = Field(default="")
    threshold: str = Field(default="")
    severity: str = Field(default="MAJOR", description="CRITICAL | MAJOR | MINOR")
    message: str = Field(default="", description="Explanation if failed")


# ============================================================
# AUDIT REPORT — Output of the Audit Gate
# ============================================================

class AuditReport(BaseModel):
    """Complete governance audit of a final result."""
    
    rules: List[AuditRule] = Field(default_factory=list)
    rules_passed: int = Field(default=0)
    rules_failed: int = Field(default=0)
    critical_failures: int = Field(default=0)
    decision: str = Field(default="PENDING", description="PASS | BLOCKED | REFUSED")
    reasoning: str = Field(default="")
    safe_to_display: bool = Field(default=False)


# ============================================================
# EVIDENCE GRAPH — Visualization data structure
# ============================================================

class GraphNode(BaseModel):
    """A node in the evidence graph (claim or source)."""
    
    id: str
    type: str  # "claim" | "source"
    label: str = ""
    # Claim-specific
    text: str = ""
    confidence: float = 0.0
    verified: bool = False
    # Source-specific
    url: str = ""
    source_type: str = ""
    credibility_score: float = 0.0


class GraphEdge(BaseModel):
    """An edge in the evidence graph."""
    
    source_id: str  # from
    target_id: str  # to
    relationship: str = "supported_by"
    verified: bool = False


class EvidenceGraph(BaseModel):
    """The complete evidence graph."""
    
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    stats: dict = Field(default_factory=dict)


# ============================================================
# REFUSAL MESSAGE — What to show users when we can't answer
# ============================================================

class RefusalMessage(BaseModel):
    """A clear, helpful refusal shown to users."""
    
    title: str = Field(default="I cannot answer this safely")
    reason: str = Field(default="")
    details: str = Field(default="")
    level: str = Field(default="HARD", description="SOFT | HARD")
    next_steps: List[str] = Field(default_factory=list)
    trusted_sources: List[dict] = Field(default_factory=list)
    emergency_note: str = Field(default="")
    failed_rules: List[str] = Field(default_factory=list)
    original_question: str = Field(default="")


print("[schemas] Loaded all 17 models: Source, Claim, AgentStep, ResearchAnswer, SearchResult, Issue, Critique, VerificationResult, VerificationReport, FinalResult, AuditRule, AuditReport, GraphNode, GraphEdge, EvidenceGraph, RefusalMessage")