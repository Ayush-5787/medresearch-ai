"""
MedResearch AI — Streamlit UI
The governed multi-agent research interface.
"""

import asyncio
import streamlit as st
import time
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator import MedResearchPipeline
from governance.audit_gate import AuditGate
from governance.refusal import RefusalBuilder
from governance.evidence_graph import EvidenceGraphBuilder


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="MedResearch AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #00d4ff;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #888;
        margin-bottom: 2rem;
    }
    .agent-box {
        background: #1a1a1a;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #00d4ff;
        margin: 0.5rem 0;
    }
    .status-pass {
        background: #0a3d0a;
        color: #4ade80;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: 600;
    }
    .status-block {
        background: #3d3d0a;
        color: #fbbf24;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: 600;
    }
    .status-refuse {
        background: #3d0a0a;
        color: #f87171;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: 600;
    }
    .refusal-box {
        background: #1a0a0a;
        border: 2px solid #f87171;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .metric-card {
        background: #1a1a1a;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #00d4ff;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("### 🏥 MedResearch AI")
    st.markdown("---")

    st.markdown("**About**")
    st.markdown(
        "A governed multi-agent research system that answers "
        "medical questions with traceable, verified citations."
    )

    st.markdown("---")
    st.markdown("**Pipeline**")
    st.markdown("""
    1. 🔍 Search Agent — finds sources
    2. 📖 Reader Agent — extracts claims
    3. ✍️ Writer Agent — drafts answer
    4. 🔎 Critic Agent — quality check
    5. 🔧 Revision Agent — fixes issues
    6. ✅ Verifier Agent — verifies claims
    """)

    st.markdown("---")
    st.markdown("**Governance**")
    st.markdown("""
    - 6 governance rules enforced
    - Refuses when uncertain
    - Always cites sources
    """)

    st.markdown("---")
    st.markdown("**Links**")
    st.markdown("[GitHub Repo](https://github.com/Ayush-5787/medresearch-ai)")
    st.markdown("[Built by Ayush Nandan](https://github.com/Ayush-5787)")

    st.markdown("---")
    st.caption("Powered by Groq · Tavily · PubMed")


# ============================================================
# HEADER
# ============================================================

st.markdown('<div class="main-header">🏥 MedResearch AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Governed Multi-Agent Research System</div>', unsafe_allow_html=True)


# ============================================================
# SAMPLE QUESTIONS
# ============================================================

st.markdown("**Try these questions:**")
sample_cols = st.columns(3)
sample_questions = [
    "What are the side effects of metformin?",
    "How does aspirin affect heart health?",
    "What are the symptoms of diabetes?",
]

clicked_question = None
for i, q in enumerate(sample_questions):
    with sample_cols[i]:
        if st.button(q, key=f"sample_{i}", use_container_width=True):
            clicked_question = q


# ============================================================
# INPUT
# ============================================================

st.markdown("---")

default_q = clicked_question or "What are the side effects of metformin?"
question = st.text_input(
    "🔎 Ask a medical question:",
    value=default_q,
    placeholder="e.g., What are the side effects of metformin?",
)

col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    run_button = st.button("🔍 Research", type="primary", use_container_width=True)
with col2:
    clear_button = st.button("🗑️ Clear", use_container_width=True)

if clear_button:
    st.rerun()


# ============================================================
# PIPELINE EXECUTION
# ============================================================

async def run_pipeline(question: str):
    """Run the full pipeline."""
    pipeline = MedResearchPipeline()
    return await pipeline.run(question, verbose=False)


if run_button and question:
    st.markdown("---")

    with st.spinner("🔄 Running 6-agent pipeline... This takes ~2-3 minutes."):
        stages = [
            "🔍 Search Agent — finding sources...",
            "📖 Reader Agent — extracting claims...",
            "✍️ Writer Agent — drafting answer...",
            "🔎 Critic Agent — reviewing quality...",
            "🔧 Revision Agent — fixing issues...",
            "✅ Verifier Agent — verifying claims...",
        ]

        start_time = time.time()

        try:
            result = asyncio.run(run_pipeline(question))
        except Exception as e:
            st.error(f"Pipeline error: {e}")
            st.stop()

    elapsed = time.time() - start_time

    # Run audit gate
    audit_gate = AuditGate()
    audit_report = audit_gate.evaluate(result)

    # ==========================================================
    # TIMELINE
    # ==========================================================

    st.markdown("### ⏱️ Agent Timeline")

    timeline_data = [
        ("🔍 Search Agent", f"{len(result.sources)} sources", result.stage_timings.get("search_ms", 0)),
        ("📖 Reader Agent", f"{len(result.claims)} claims", result.stage_timings.get("reader_ms", 0)),
        ("✍️ Writer Agent", f"{len(result.answer)} chars", result.stage_timings.get("writer_ms", 0)),
        ("🔎 Critic Agent", f"{result.critique.status} ({result.critique.overall_score:.2f})", result.stage_timings.get("critic_ms", 0)),
        ("🔧 Revision Agent", "skipped" if result.stage_timings.get("revision_ms", 0) == 0 else "applied", result.stage_timings.get("revision_ms", 0)),
        ("✅ Verifier Agent", f"{result.verification.verified_count}/{result.verification.total_claims} verified", result.stage_timings.get("verifier_ms", 0)),
    ]

    for agent, detail, ms in timeline_data:
        st.markdown(
            f'<div class="agent-box">'
            f'<strong>{agent}</strong> &nbsp;→&nbsp; {detail} &nbsp;&nbsp; '
            f'<span style="color:#888; font-size:0.85rem;">{ms}ms</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    # ==========================================================
    # STATUS METRICS
    # ==========================================================

    st.markdown("---")
    status_col1, status_col2, status_col3, status_col4 = st.columns(4)

    with status_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{result.confidence:.2f}</div>
            <div class="metric-label">Confidence</div>
        </div>
        """, unsafe_allow_html=True)

    with status_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{result.total_duration_ms // 1000}s</div>
            <div class="metric-label">Total Time</div>
        </div>
        """, unsafe_allow_html=True)

    with status_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{result.verification.verified_count}/{result.verification.total_claims}</div>
            <div class="metric-label">Verified</div>
        </div>
        """, unsafe_allow_html=True)

    with status_col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{audit_report.rules_passed}/6</div>
            <div class="metric-label">Rules Passed</div>
        </div>
        """, unsafe_allow_html=True)

    # ==========================================================
    # DECISION PANEL
    # ==========================================================

    st.markdown("---")

    if audit_report.decision == "PASS":
        st.markdown('<div class="status-pass">✅ PASS — All governance rules passed</div>', unsafe_allow_html=True)
    elif audit_report.decision == "BLOCKED":
        st.markdown('<div class="status-block">⚠️ BLOCKED — Answer shown with warnings</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-refuse">🚫 REFUSED — Answer not safe to display</div>', unsafe_allow_html=True)

    # ==========================================================
    # ANSWER OR REFUSAL
    # ==========================================================

    if audit_report.decision in ("PASS", "BLOCKED"):
        st.markdown("### 📝 Answer")
        st.markdown(result.answer)

        with st.expander(f"📊 Verification Report ({result.verification.verified_count}/{result.verification.total_claims} verified)"):
            for v in result.verification.results:
                icon = {"VERIFIED": "✅", "PARTIALLY_VERIFIED": "🟡", "NOT_VERIFIED": "🔴", "CONTRADICTED": "⚠️"}.get(v.verdict, "❓")
                st.markdown(f"**{icon} Claim {v.claim_index + 1}:** {v.claim_text[:120]}...")
                st.caption(f"Verdict: {v.verdict} ({v.confidence:.2f})")
                if v.evidence:
                    st.caption(f"Evidence: {v.evidence[:200]}...")
                st.markdown("---")
    else:
        refusal_builder = RefusalBuilder()
        refusal = refusal_builder.build(result, audit_report)

        st.markdown(f"""
        <div class="refusal-box">
            <h3 style="color: #f87171;">⚠️ {refusal.title}</h3>
            <p><strong>Reason:</strong> {refusal.reason}</p>
            <p><strong>Details:</strong> {refusal.details}</p>
            <h4>What you can do:</h4>
            <ol>
                {''.join(f'<li>{s}</li>' for s in refusal.next_steps)}
            </ol>
            <h4>Trusted sources:</h4>
            <ul>
                {''.join(f'<li><a href="{s["url"]}" target="_blank">{s["name"]}</a> — {s["why"]}</li>' for s in refusal.trusted_sources)}
            </ul>
            <p style="color: #f87171;"><strong>🚨 {refusal.emergency_note}</strong></p>
        </div>
        """, unsafe_allow_html=True)

    # ==========================================================
    # GOVERNANCE REPORT
    # ==========================================================

    st.markdown("---")
    st.markdown("### 🛡️ Governance Report")

    for rule in audit_report.rules:
        icon = "✅" if rule.passed else "❌"
        with st.expander(f"{icon} {rule.rule_id}: {rule.name}"):
            st.write(f"**Actual:** {rule.actual_value}")
            st.write(f"**Threshold:** {rule.threshold}")
            st.write(f"**Severity:** {rule.severity}")
            if rule.message:
                st.write(f"**Message:** {rule.message}")

    # ==========================================================
    # EVIDENCE GRAPH
    # ==========================================================

    st.markdown("---")
    st.markdown("### 🕸️ Evidence Graph")

    builder = EvidenceGraphBuilder()
    graph = builder.build(result)

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Claims", graph.stats["total_claims"])
    with col_b:
        st.metric("Sources", graph.stats["total_sources"])
    with col_c:
        st.metric("Citations", graph.stats["total_edges"])

    st.markdown("**Claims → Sources**")
    claim_to_sources = {}
    for edge in graph.edges:
        claim_to_sources.setdefault(edge.source_id, []).append(edge.target_id)

    for i, claim in enumerate(result.claims[:10]):
        claim_id = f"claim_{i+1}"
        sources = claim_to_sources.get(claim_id, [])
        if sources:
            with st.expander(f"Claim {i+1}: {claim.text[:80]}..."):
                st.write(f"**Full claim:** {claim.text}")
                st.write(f"**Confidence:** {claim.confidence:.2f}")
                st.write(f"**Supported by:** {len(sources)} source(s)")

    st.caption(f"Total: {len(result.claims)} claims connected to {len(result.sources)} sources via {len(graph.edges)} citations")

    # ==========================================================
    # DISCLAIMER
    # ==========================================================

    st.markdown("---")
    st.caption(f"⚠️ {result.disclaimer}")


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.caption("MedResearch AI — Built by Ayush Nandan | [GitHub](https://github.com/Ayush-5787/medresearch-ai)")