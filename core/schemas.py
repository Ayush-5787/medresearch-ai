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


print("[schemas] Loaded data models: Source, Claim, AgentStep, ResearchAnswer, SearchResult, Issue, Critique")
