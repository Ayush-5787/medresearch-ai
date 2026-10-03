"""
MedResearch AI — Streamlit UI (Multi-Language + Voice + Image + PDF + Auth + Cache)
"""

from dotenv import load_dotenv
from pathlib import Path

# Load environment variables FIRST, before any other imports
load_dotenv(Path(__file__).parent.parent / ".env")

import asyncio
import streamlit as st
import time
from datetime import datetime
import sys

# NEW — for embedding the architecture viewer
import streamlit.components.v1 as components
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator import MedResearchPipeline
from governance.audit_gate import AuditGate
from governance.refusal import RefusalBuilder
from governance.evidence_graph import EvidenceGraphBuilder
from core.language import LanguageHandler
from core.country import CountryConfig
from core.voice import VoiceHandler
from multimodal.image_reader import ImageReader
from reports.pdf_generator import PDFReportGenerator
from auth.auth_gate import render_login_screen, logout, init_session
from cache.cache_manager import CacheManager


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="MedResearch AI",
    page_icon=str(Path(__file__).parent.parent / "docs" / "logo.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE
# ============================================================

if "view" not in st.session_state:
    st.session_state.view = "main"

# Persist last result across Streamlit reruns (button clicks)
if "result" not in st.session_state:
    st.session_state.result = None
if "audit_report" not in st.session_state:
    st.session_state.audit_report = None
if "cached" not in st.session_state:
    st.session_state.cached = None


# ============================================================
# AUTHENTICATION GATE
# ============================================================

init_session()

if not st.session_state.get("authenticated", False):
    render_login_screen()
    st.stop()


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 700; color: #00d4ff; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1rem; color: #888; margin-bottom: 2rem; }
    .agent-box { background: #1a1a1a; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #00d4ff; margin: 0.5rem 0; }
    .status-pass { background: #0a3d0a; color: #4ade80; padding: 0.5rem 1rem; border-radius: 0.5rem; font-weight: 600; }
    .status-block { background: #3d3d0a; color: #fbbf24; padding: 0.5rem 1rem; border-radius: 0.5rem; font-weight: 600; }
    .status-refuse { background: #3d0a0a; color: #f87171; padding: 0.5rem 1rem; border-radius: 0.5rem; font-weight: 600; }
    .refusal-box { background: #1a0a0a; border: 2px solid #f87171; padding: 1.5rem; border-radius: 0.5rem; margin: 1rem 0; }
    .metric-card { background: #1a1a1a; padding: 1rem; border-radius: 0.5rem; text-align: center; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #00d4ff; }
    .metric-label { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .lang-country-box { background: #1a1a1a; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; }
    .image-box { background: #0a2a1a; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; border: 1px solid #4ade80; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# INITIALIZE HANDLERS
# ============================================================

@st.cache_resource
def get_handlers():
    return LanguageHandler(), CountryConfig(), VoiceHandler(), ImageReader(), PDFReportGenerator()

lang_handler, country_handler, voice_handler, image_reader, pdf_generator = get_handlers()


@st.cache_resource
def get_cache():
    return CacheManager()

response_cache = get_cache()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.image(str(Path(__file__).parent.parent / "docs" / "logo.png"), width=120)
    st.markdown("### MedResearch AI")

    user = st.session_state.get("user", {})
    if user:
        st.markdown(f"👤 **{user.get('username', 'User')}**")
        st.caption(f"📧 {user.get('email', '')[:30]}")

    st.markdown("---")

    if st.button("🚪 Logout", use_container_width=True):
        logout()

    # ============================================================
    # NEW — INTERACTIVE ARCHITECTURE VIEWER
    # ============================================================
    st.markdown("---")
    ARCH_URL = "https://ayush-5787.github.io/medresearch-ai/architecture.html"

    st.link_button(
        "🏛 Explore System Architecture",
        url=ARCH_URL,
        use_container_width=True,
        help="Live 3D simulation — every component performs its duty. Click panels for explanations.",
    )

    with st.expander("👁 View inside app"):
        arch_html = None
        try:
            with urlopen(ARCH_URL, timeout=6) as resp:
                arch_html = resp.read().decode("utf-8")
        except Exception:
            local_arch = Path(__file__).parent.parent / "architecture.html"
            if local_arch.exists():
                arch_html = local_arch.read_text(encoding="utf-8")

        if arch_html:
            components.html(arch_html, height=640, scrolling=False)
            st.caption("💡 For the full-screen experience, use the button above.")
        else:
            st.caption("⚠️ Viewer unavailable offline — use the button above when online.")
    # ============================================================
    # END NEW
    # ============================================================

    st.markdown("---")
    st.markdown("**About**")
    st.markdown(
        "A governed multi-agent research system that answers "
        "medical questions with traceable, verified citations. "
        "Supports 71 languages, voice output, image input, and PDF export."
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
    st.markdown("**Features**")
    st.markdown("""
    - 🌐 Multi-language (71 languages)
    - 🔊 Voice output (30 languages)
    - 📷 Image upload (OCR)
    - 📄 PDF report download
    - 🛡️ Governance (6 rules)
    - ✅ Per-claim verification
    - ⚡ Response cache (saves tokens)
    """)
    st.markdown("---")
    st.markdown("**⚡ Cache Stats**")
    try:
        cache_stats = response_cache.stats()
        st.caption(f"📦 {cache_stats['total_entries']} entries")
        st.caption(f"🎯 {cache_stats['total_hits']} hits saved")
    except Exception:
        st.caption("📦 0 entries")

    if st.button("🧹 Clear Cache", use_container_width=True, key="clear_cache_btn"):
        try:
            cleared = response_cache.clear()
            st.success(f"Cleared {cleared} entries")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("---")
    st.markdown("**Links**")
    st.markdown("[GitHub Repo](https://github.com/Ayush-5787/medresearch-ai)")
    st.caption("Powered by Groq · Tavily · PubMed · Tesseract")


# ============================================================
# HEADER
# ============================================================

col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image(str(Path(__file__).parent.parent / "docs" / "logo.png"), width=80)
with col_title:
    st.markdown('<div class="main-header">MedResearch AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Governed Multi-Agent Research System — 71 Languages, Voice, Image, PDF</div>', unsafe_allow_html=True)


# ============================================================
# LANGUAGE & COUNTRY SELECTORS
# ============================================================

st.markdown('<div class="lang-country-box">', unsafe_allow_html=True)
col_lang, col_country, col_spacer = st.columns([1, 1, 2])

with col_lang:
    languages = {"auto": "🌐 Auto-detect"}
    for code, name in lang_handler.list_languages().items():
        languages[code] = f"{name} ({code})"
    selected_lang = st.selectbox(
        "🌐 Language",
        options=list(languages.keys()),
        format_func=lambda x: languages[x],
        index=0,
    )

with col_country:
    countries = {"DEFAULT": "🌍 International"}
    for c in country_handler.list_countries():
        countries[c["code"]] = f"{c['name']} ({c['code']})"
    selected_country = st.selectbox(
        "🌍 Country",
        options=list(countries.keys()),
        format_func=lambda x: countries[x],
        index=0,
    )
st.markdown('</div>', unsafe_allow_html=True)

country_info = country_handler.get(selected_country)
if country_info:
    st.caption(
        f"📍 Emergency: **{country_info.get('emergency')}** · "
        f"Sources: {', '.join(s['name'] for s in country_info.get('trusted_sources', [])[:3])}"
    )


# ============================================================
# IMAGE UPLOAD
# ============================================================

st.markdown("---")
st.markdown("### 📷 Upload Medical Image (Optional)")
st.caption("Upload a photo of a prescription, medicine box, or medical report. Text will be extracted automatically.")

with st.container():
    st.markdown('<div class="image-box">', unsafe_allow_html=True)

    uploaded_image = st.file_uploader(
        "Choose an image...",
        type=["jpg", "jpeg", "png", "bmp", "tiff"],
        key="image_upload",
    )

    if uploaded_image is not None:
        col_img, col_text = st.columns([1, 2])
        with col_img:
            st.image(uploaded_image, caption="Uploaded image", width=250)
        with col_text:
            with st.spinner("🔄 Extracting text from image..."):
                image_bytes = uploaded_image.getvalue()
                ocr_lang = "eng+hin" if selected_lang == "hi" else "eng"
                result = image_reader.extract_text(image_bytes, lang=ocr_lang)

            if result["error"]:
                st.error(f"❌ OCR error: {result['error']}")
                extracted_image_text = ""
            elif result["text"]:
                st.success(f"✅ Extracted ({result['word_count']} words, confidence {result['confidence']}):")
                st.info(f"**{result['text']}**")
                extracted_image_text = result["text"]
            else:
                st.warning("⚠️ No text detected in image.")
                extracted_image_text = ""

    else:
        extracted_image_text = ""

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# SAMPLE QUESTIONS
# ============================================================

st.markdown("**Try these questions:**")
sample_cols = st.columns(4)
sample_questions = [
    ("🇬🇧 English", "What are the side effects of metformin?"),
    ("🇮🇳 हिन्दी", "मेटफॉर्मिन के दुष्प्रभाव क्या हैं?"),
    ("🇪🇸 Español", "¿Cuáles son los efectos secundarios de la metformina?"),
    ("🇫🇷 Français", "Quels sont les effets secondaires de la metformine?"),
]

clicked_question = None
for i, (label, q) in enumerate(sample_questions):
    with sample_cols[i]:
        if st.button(label, key=f"sample_{i}", use_container_width=True):
            clicked_question = q


# ============================================================
# TEXT INPUT
# ============================================================

st.markdown("---")
st.markdown("### ⌨️ Ask Your Question")

if clicked_question:
    default_q = clicked_question
elif extracted_image_text:
    default_q = extracted_image_text
else:
    default_q = "What are the side effects of metformin?"

question = st.text_area(
    "🔎 Ask a medical question (any language):",
    value=default_q,
    height=80,
    placeholder="e.g., What are the side effects of metformin? / मेटफॉर्मिन के दुष्प्रभाव क्या हैं?",
)

col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    run_button = st.button("🔍 Research", type="primary", use_container_width=True)
with col2:
    clear_button = st.button("🗑️ Clear", use_container_width=True)

if clear_button:
    st.session_state.result = None
    st.session_state.audit_report = None
    st.session_state.cached = None
    st.rerun()


# ============================================================
# PIPELINE EXECUTION
# ============================================================

async def run_pipeline(question: str, language: str, country: str):
    pipeline = MedResearchPipeline()
    return await pipeline.run(question, language=language, country=country, verbose=False)


if run_button and question:
    # Check cache first
    cached = None
    try:
        cached = response_cache.get(question, selected_lang, selected_country)
    except Exception as e:
        st.warning(f"Cache read error: {e}")

    if cached:
        # ---------- CACHE HIT ----------
        class _V:
            def __init__(self, data):
                results = data.get("results", []) if isinstance(data, dict) else []
                self.results = results
                self.verified_count = sum(
                    1 for r in results if (r.get("verdict") if isinstance(r, dict) else None) == "VERIFIED"
                )
                self.total_claims = len(results)

        class _C:
            def __init__(self, conf):
                self.status = "PASS"
                self.overall_score = conf

        class CachedResult:
            def __init__(self, data):
                self.question = data.get("question", "")
                self.answer = data["answer"]
                self.confidence = data["confidence"] or 0.0
                self.decision = data["decision"]
                self.sources = data["sources"]
                self.claims = data["claims"]
                self.verification = _V(data.get("verification", {}))
                self.critique = _C(data["confidence"] or 0.0)
                self.stage_timings = {}
                self.total_duration_ms = 0
                self.disclaimer = "This answer was retrieved from cache."

        class _A:
            def __init__(self, decision):
                self.decision = decision
                self.rules_passed = 6
                self.rules = []

        st.session_state.result = CachedResult(cached)
        st.session_state.audit_report = _A(cached["decision"])
        st.session_state.cached = cached
    else:
        # ---------- CACHE MISS ----------
        with st.spinner("🔄 Running 6-agent pipeline... This takes ~2-3 minutes."):
            try:
                result = asyncio.run(run_pipeline(question, selected_lang, selected_country))
            except Exception as e:
                st.error(f"Pipeline error: {e}")
                st.stop()

        audit_gate = AuditGate()
        audit_report = audit_gate.evaluate(result)

        try:
            saved = response_cache.set(question, selected_lang, selected_country, result)
            if saved:
                st.caption("💾 Answer saved to cache — future identical questions will be instant")
        except Exception as e:
            st.caption(f"⚠️ Could not save to cache: {e}")

        st.session_state.result = result
        st.session_state.audit_report = audit_report
        st.session_state.cached = None

    st.rerun()


# ============================================================
# RENDER RESULT (persists across reruns via session_state)
# ============================================================

if st.session_state.get("result") is not None:
    result = st.session_state.result
    audit_report = st.session_state.audit_report
    cached = st.session_state.get("cached")

    st.markdown("---")

    if cached:
        st.success(
            f"⚡ **Instant answer from cache** — 0 tokens used · "
            f"Asked **{cached['hit_count']}** time(s) before"
        )

    # ---------- TIMELINE ----------
    st.markdown("### ⏱️ Agent Timeline")
    timeline_data = [
        ("🔍 Search Agent", f"{len(result.sources)} sources", result.stage_timings.get("search_ms", 0)),
        ("📖 Reader Agent", f"{len(result.claims)} claims", result.stage_timings.get("reader_ms", 0)),
        ("✍️ Writer Agent", f"{len(result.answer)} chars", result.stage_timings.get("writer_ms", 0)),
        ("🔎 Critic Agent", f"{result.critique.status} ({result.critique.overall_score:.2f})", result.stage_timings.get("critic_ms", 0)),
        ("🔧 Revision Agent", "skipped" if result.stage_timings.get("revision_ms", 0) == 0 else "applied", result.stage_timings.get("revision_ms", 0)),
        ("✅ Verifier Agent", f"{result.verification.verified_count}/{result.verification.total_claims} verified", result.stage_timings.get("verifier_ms", 0)),
    ]
    if "translate_to_en_ms" in result.stage_timings:
        timeline_data.insert(0, ("🌐 Translate → EN", "input translated", result.stage_timings["translate_to_en_ms"]))
    if "translate_from_en_ms" in result.stage_timings:
        timeline_data.append(("🌐 Translate ← back", "answer translated", result.stage_timings["translate_from_en_ms"]))

    for agent, detail, ms in timeline_data:
        st.markdown(
            f'<div class="agent-box"><strong>{agent}</strong> &nbsp;→&nbsp; {detail} &nbsp;&nbsp; '
            f'<span style="color:#888; font-size:0.85rem;">{ms}ms</span></div>',
            unsafe_allow_html=True
        )

    # ---------- METRICS ----------
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{result.confidence:.2f}</div><div class="metric-label">Confidence</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{result.total_duration_ms // 1000}s</div><div class="metric-label">Total Time</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{result.verification.verified_count}/{result.verification.total_claims}</div><div class="metric-label">Verified</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{audit_report.rules_passed}/6</div><div class="metric-label">Rules Passed</div></div>', unsafe_allow_html=True)

    # ---------- DECISION ----------
    st.markdown("---")
    if audit_report.decision == "PASS":
        st.markdown('<div class="status-pass">✅ PASS — All governance rules passed</div>', unsafe_allow_html=True)
    elif audit_report.decision == "BLOCKED":
        st.markdown('<div class="status-block">⚠️ BLOCKED — Answer shown with warnings</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-refuse">🚫 REFUSED — Answer not safe to display</div>', unsafe_allow_html=True)

    # ---------- ANSWER OR REFUSAL ----------
    if audit_report.decision in ("PASS", "BLOCKED"):
        st.markdown("### 📝 Answer")
        st.markdown(result.answer)

        # ---------- VOICE ----------
        st.markdown("### 🔊 Listen to Answer")
        st.caption("Hear the answer read aloud in your language.")

        try:
            answer_lang = selected_lang if selected_lang != "auto" else lang_handler.detect_language(result.answer)
        except Exception:
            answer_lang = "en"

        voice_cols = st.columns(3)
        with voice_cols[0]:
            if st.button("🔊 Original language", key="tts_original", use_container_width=True):
                with st.spinner("Generating audio..."):
                    audio_bytes = voice_handler.synthesize(result.answer, answer_lang)
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
        with voice_cols[1]:
            if st.button("🔊 English", key="tts_en", use_container_width=True):
                with st.spinner("Generating audio..."):
                    audio_bytes = voice_handler.synthesize(result.answer, "en")
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
        with voice_cols[2]:
            if st.button("🔊 हिन्दी", key="tts_hi", use_container_width=True):
                with st.spinner("Generating audio..."):
                    audio_bytes = voice_handler.synthesize(result.answer, "hi")
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)

        # ---------- PDF ----------
        st.markdown("### 📄 Download Report")
        st.caption("Download a professional PDF with the answer, sources, verification, and governance report.")

        try:
            pdf_bytes = pdf_generator.generate(
                result,
                audit_report,
                language=selected_lang if selected_lang != "auto" else "en",
                country=selected_country,
            )

            if pdf_bytes:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"medresearch_report_{timestamp}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.warning("⚠️ PDF generation failed. Please try again.")
        except Exception as e:
            st.warning(f"⚠️ PDF error: {str(e)[:100]}")

        # ---------- VERIFICATION ----------
        with st.expander(f"📊 Verification Report ({result.verification.verified_count}/{result.verification.total_claims} verified)"):
            for v in result.verification.results:
                if isinstance(v, dict):
                    verdict = v.get("verdict", "UNKNOWN")
                    claim_idx = v.get("claim_index", 0)
                    claim_text = v.get("claim_text", "")
                    conf = v.get("confidence", 0.0)
                    evidence = v.get("evidence", "")
                else:
                    verdict = v.verdict
                    claim_idx = v.claim_index
                    claim_text = v.claim_text
                    conf = v.confidence
                    evidence = getattr(v, "evidence", "")

                icon = {"VERIFIED": "✅", "PARTIALLY_VERIFIED": "🟡", "NOT_VERIFIED": "🔴", "CONTRADICTED": "⚠️"}.get(verdict, "❓")
                st.markdown(f"**{icon} Claim {claim_idx + 1}:** {claim_text[:120]}...")
                st.caption(f"Verdict: {verdict} ({conf:.2f})")
                if evidence:
                    st.caption(f"Evidence: {evidence[:200]}...")
                st.markdown("---")
    else:
        # ---------- REFUSAL ----------
        refusal_builder = RefusalBuilder()
        try:
            refusal = refusal_builder.build(result, audit_report)
        except Exception:
            refusal = type("R", (), {
                "title": "Refused",
                "reason": "This question cannot be answered safely.",
                "details": "Please consult a qualified professional.",
                "next_steps": ["Consult a doctor"],
                "trusted_sources": [],
                "emergency_note": "Call your local emergency number if urgent.",
            })()

        st.markdown(f"""
        <div class="refusal-box">
            <h3 style="color: #f87171;">⚠️ {refusal.title}</h3>
            <p><strong>Reason:</strong> {refusal.reason}</p>
            <p><strong>Details:</strong> {refusal.details}</p>
            <h4>What you can do:</h4>
            <ol>{''.join(f'<li>{s}</li>' for s in refusal.next_steps)}</ol>
            <h4>Trusted sources:</h4>
            <ul>{''.join(f'<li><a href="{s["url"]}" target="_blank">{s["name"]}</a> — {s["why"]}</li>' for s in refusal.trusted_sources)}</ul>
            <p style="color: #f87171;"><strong>🚨 {refusal.emergency_note}</strong></p>
        </div>
        """, unsafe_allow_html=True)

    # ---------- GOVERNANCE ----------
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

    # ---------- EVIDENCE GRAPH ----------
    if result.claims:
        st.markdown("---")
        st.markdown("### 🕸️ Evidence Graph")
        builder = EvidenceGraphBuilder()
        try:
            graph = builder.build(result)
            ca, cb, cc = st.columns(3)
            with ca:
                st.metric("Claims", graph.stats["total_claims"])
            with cb:
                st.metric("Sources", graph.stats["total_sources"])
            with cc:
                st.metric("Citations", graph.stats["total_edges"])

            st.markdown("**Claims → Sources**")
            claim_to_sources = {}
            for edge in graph.edges:
                claim_to_sources.setdefault(edge.source_id, []).append(edge.target_id)
            for i, claim in enumerate(result.claims[:10]):
                cid = f"claim_{i+1}"
                sources = claim_to_sources.get(cid, [])
                if sources:
                    claim_text = claim.text if hasattr(claim, "text") else str(claim)
                    with st.expander(f"Claim {i+1}: {claim_text[:80]}..."):
                        st.write(f"**Full claim:** {claim_text}")
                        st.write(f"**Supported by:** {len(sources)} source(s)")
        except Exception as e:
            st.caption(f"Evidence graph unavailable for cached result: {str(e)[:80]}")

    st.caption(f"Total: {len(result.claims)} claims connected to {len(result.sources)} sources")
    st.markdown("---")
    st.caption(f"⚠️ {result.disclaimer}")


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
# NEW — added architecture link to footer
st.caption("MedResearch AI — Built by Ayush Nandan | [GitHub](https://github.com/Ayush-5787/medresearch-ai) | [🏛 Architecture](https://ayush-5787.github.io/medresearch-ai/architecture.html)")