"""
MedResearch AI — Briefing PDF Generator
Produces a professional PDF of the complete project briefing + 70-question Q&A bank.
Uses ReportLab (already a project dependency).
"""

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from pathlib import Path
from datetime import datetime


# ---------- COLORS ----------
CYAN = HexColor("#00b8d4")
DARK = HexColor("#0a0e1a")
GREY = HexColor("#666666")
LIGHT_GREY = HexColor("#f5f5f5")
GREEN = HexColor("#16a34a")
RED = HexColor("#dc2626")


# ---------- STYLES ----------
def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="CoverTitle", fontSize=32, leading=38,
        textColor=CYAN, fontName="Helvetica-Bold", alignment=TA_LEFT,
        spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="CoverSub", fontSize=14, leading=20,
        textColor=GREY, fontName="Helvetica", alignment=TA_LEFT,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="H1", fontSize=20, leading=26,
        textColor=DARK, fontName="Helvetica-Bold",
        spaceBefore=18, spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="H2", fontSize=14, leading=20,
        textColor=CYAN, fontName="Helvetica-Bold",
        spaceBefore=14, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Body", fontSize=10.5, leading=15,
        textColor=black, fontName="Helvetica", alignment=TA_JUSTIFY,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="Q", fontSize=10.5, leading=15,
        textColor=DARK, fontName="Helvetica-Bold",
        spaceBefore=10, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="A", fontSize=10, leading=14,
        textColor=black, fontName="Helvetica", alignment=TA_JUSTIFY,
        leftIndent=14, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="Quote", fontSize=10, leading=14,
        textColor=DARK, fontName="Helvetica-Oblique", alignment=TA_JUSTIFY,
        leftIndent=14, rightIndent=14, spaceBefore=6, spaceAfter=8,
        borderColor=CYAN, borderWidth=0, borderPadding=6,
    ))
    return styles


# ---------- CONTENT ----------
PITCH = (
    "MedResearch AI is a governed multi-agent system that answers medical questions "
    "with traceable, verified citations. Six specialized agents research, draft, "
    "critique, and verify every answer, and a deterministic governance layer enforces "
    "six safety rules before anything reaches the user. If the system can't verify it, "
    "it refuses to show it — with trusted sources and emergency guidance instead."
)

PROBLEMS = [
    ["Problem", "Reality"],
    ["Medical misinformation kills", "People ask Dr. Google before asking doctors. Generic chatbots answer confidently even when wrong."],
    ["LLMs hallucinate", "A plain LLM will invent side effects, dosages, and studies — with no sources."],
    ["No accountability", "Most AI answers can't be traced back to evidence."],
    ["Unsafe advice", "Chatbots happily 'prescribe' — a legal and safety liability."],
]

AGENTS = [
    ["Agent", "Job", "Detail"],
    ["🔍 Search", "Find sources", "PubMed (8) + Tavily web (5); ranks 13; prefers DailyMed, MedlinePlus"],
    ["📖 Reader", "Extract claims", "Reads each source; extracts factual claims with source URLs attached"],
    ["✍️ Writer", "Draft answer", "Writes a cited answer from claims only — never from own knowledge"],
    ["🔎 Critic", "Quality check", "Scores the draft, flags issues (missing disclaimer, weak structure)"],
    ["🔧 Revision", "Fix issues", "Tiered revision — refuses to 'fix' a fundamentally broken draft"],
    ["✅ Verifier", "Verify claims", "Checks each claim vs source → VERIFIED / PARTIAL / NOT / CONTRADICTED / ERROR"],
]

GOV_RULES = [
    ["#", "Rule", "Threshold", "Severity"],
    ["1", "All claims have sources", "100%", "CRITICAL"],
    ["2", "Verification rate", "≥ 90%", "CRITICAL"],
    ["3", "Overall confidence", "≥ 0.70", "MAJOR"],
    ["4", "No unsafe language", "0 violations", "CRITICAL"],
    ["5", "Medical disclaimer present", "required", "MAJOR"],
    ["6", "Answer has substance", "≥ 200 chars", "MAJOR"],
]

TECH_STACK = [
    ["Layer", "Technology", "Why"],
    ["Language", "Python", "AI/data ecosystem"],
    ["UI", "Streamlit", "Fast, deployable, auth + components"],
    ["LLM #1", "Groq", "Extremely fast inference"],
    ["LLM #2 (fallback)", "Google Gemini", "Automatic failover on quota/429"],
    ["Medical search", "PubMed API", "Peer-reviewed literature"],
    ["Web search", "Tavily", "General medical web sources"],
    ["OCR", "Tesseract", "Reads prescriptions / medicine boxes"],
    ["Data models", "Pydantic (17 models)", "Type-safe structured data between agents"],
    ["Concurrency", "asyncio", "Non-blocking pipeline"],
    ["Config", "python-dotenv", "Secrets out of code"],
    ["Deployment", "Streamlit Cloud + GitHub", "Live demo"],
    ["Eval", "Custom run_evals.py", "Measures verification rate, refusals, latency"],
]

# ---------- NEW Q&A DATA ----------
QA_A_TRUST = [
    ("Why should anyone trust this over ChatGPT?",
     "Three structural differences: (1) Sourcing is enforced, not optional — every claim must carry a source URL, and Rule 1 blocks unsourced claims. (2) Verification is a separate stage — the Verifier checks each claim against its actual source text before display. (3) Refusal is a designed outcome — when the governance gate fails, the user gets a structured refusal with trusted sources and emergency numbers."),
    ("What does ChatGPT do that you don't?",
     "Honest answer: vastly more training data, arbitrary complexity handling, more conversational. It's a general reasoning engine. This is a narrow, governed pipeline — deliberately less capable but more accountable."),
    ("Isn't this just a wrapper around Groq/Gemini?",
     "No. The LLM is one of six components. Value is in orchestration: retrieval (PubMed + Tavily), claim extraction with source attribution, per-claim verification, deterministic governance, honest degradation. Swap the LLM and the architecture stays. Swap the architecture and safety guarantees vanish."),
    ("What stops ChatGPT from adding these features tomorrow?",
     "Nothing technical. But they face a UX constraint this doesn't: ChatGPT is optimized for broad helpfulness; refusing 'should I take X?' is bad UX for them. This project is domain-narrow enough that refusal is a feature, not a bug. That's positioning, not a moat — I'd rather be honest about that."),
    ("Why not use Perplexity or Bing Chat, which already cite?",
     "They cite sources. They don't publish per-claim verification verdicts, run a deterministic governance gate, or refuse when verification fails. This shows citations AND a verdict AND a governance decision."),
    ("If your LLM is Groq/Gemini, isn't your answer only as good as their training data?",
     "Correct — and that's an inherent limit. The Verifier checks claims against retrieved sources, not training data. Accuracy is bounded by PubMed/Tavily quality, not by the LLM's training. The LLM extracts and phrases; the sources provide truth."),
    ("Would you use this over ChatGPT for a real medical question?",
     "For a first-pass research summary with auditable sources, yes. For personal medical decisions, no — and neither should anyone use ChatGPT. Both systems say 'not a diagnosis tool.' The difference is this one enforces that stance."),
    ("How do you know ChatGPT would hallucinate on these questions?",
     "We know LLMs hallucinate; OpenAI documents this. The question isn't whether — it's whether the system catches it. Here, every claim must verify against its source. If it doesn't, the governance gate refuses."),
    ("Could a user check ChatGPT's answer themselves?",
     "Yes — but that's the point. This system shows sources per claim, so checking is one click. ChatGPT shows sources only if asked, and they're often topically related but don't contain the specific claim."),
    ("What's your unfair advantage over any other student project?",
     "Honesty about limitations. Most student AI projects claim '10/10, no bugs.' This one shows a documented 60% baseline, names the failure classes, and describes the fixes. Recruiters trust the second project more."),
]

QA_B_DATA = [
    ("What dataset does this use?",
     "There's no single training dataset. The system retrieves live at query time from two sources: PubMed E-utilities (peer-reviewed literature) and Tavily (web search filtered toward trusted medical domains). Retrieval is per-question, not pre-indexed."),
    ("How is data collected?",
     "Four retrieval modes: (1) PubMed API — paper titles, abstracts, PMIDs. (2) Tavily API — web search with snippets. (3) Full-text scraping — httpx + BeautifulSoup fetch and parse HTML. (4) Tesseract OCR — user-uploaded images converted to text."),
    ("Is the data pre-processed or raw?",
     "Raw at retrieval, structured at extraction. The Reader Agent takes source text and asks the LLM to extract discrete factual claims — each becomes a Claim object with text, source_urls, confidence, and verification_notes."),
    ("Do you have a labeled dataset for evaluation?",
     "Partially. evals/test_cases.json contains 15 hand-curated test cases across 7 categories. Each case has an expected decision (PASS/REFUSED) and check assertions. Small but real — expandable to 100+ cases."),
    ("How do you ensure sources are trustworthy?",
     "Three filters: (1) PubMed is inherently peer-reviewed. (2) Tavily results are ranked by domain credibility — DailyMed, MedlinePlus, NIH, WHO score higher than blogs. (3) The Source model carries credibility_score, and Search Agent prefers high-credibility domains."),
    ("What if PubMed doesn't cover a topic?",
     "Tavily web search fills the gap. For niche topics coverage can be thin — and the honest behavior is to refuse when verification rate < 90%. We'd rather refuse than fabricate."),
    ("Do you store any user data?",
     "users.db stores username, email, and bcrypt-hashed password. response_cache.db stores cached answers keyed by SHA256(question+lang+country). Both are SQLite on Streamlit Cloud and reset on redeploy — a known limitation."),
    ("How would you build a proper training dataset from this?",
     "The eval suite is the seed. With a larger corpus of (question, expected_decision, expected_verification_rate) triples, you could fine-tune a small classification model to pre-screen questions."),
]

QA_C_BUSINESS = [
    ("Who would use this in the real world?",
     "Three segments: (1) Medical students/residents needing cited literature summaries. (2) Health journalists needing verifiable sourcing. (3) Patients researching a condition needing trustworthy summaries with 'consult a doctor' framing. Not a replacement for clinical judgment — an evidence-finding tool."),
    ("How would this make money?",
     "Three plausible models: (1) Freemium — free with rate limits, paid for unlimited + PDF. (2) B2B API — sell the pipeline to health-tech. (3) Enterprise white-label — hospitals license for internal research. None pursued yet; this is a portfolio project."),
    ("What's the biggest real-world risk?",
     "Users trusting it too much. A medically-worded answer, even with citations and disclaimers, can feel like advice. The refusal UX, disclaimer, and 'not a diagnosis tool' framing exist precisely because over-trust is the risk, not under-trust."),
    ("Would a hospital actually deploy this?",
     "Not as-is. Hospitals require HIPAA compliance, audit logs, clinician sign-off, and validation studies. This has the architecture but not the certification. Path: portfolio → pilot with research lab → clinical validation → hospital deployment."),
    ("What's the impact if it works?",
     "If someone researching a drug interaction gets an answer with three citations they can read instead of a confident hallucination they believe — that's the win. Small, specific, real."),
    ("What's the killer feature?",
     "The refusal-with-alternatives UX. Not just 'I can't answer' — it says 'here's why, here's what to do, here's who to ask, here's your country's emergency number.' Most safety systems say no. This says no and helps."),
]

QA_D_ETHICS = [
    ("Is this compliant with medical regulations?",
     "No — and it doesn't claim to be. It's a research tool with disclaimers. Real medical software (FDA class II, CE marking) requires clinical validation this doesn't have. Calling it 'a research tool' is a legally meaningful claim, not marketing language."),
    ("How do you handle bias in medical sources?",
     "PubMed and Tavily have known biases (Western literature dominance, English-language bias, publication bias). This project inherits them. Mitigations: disclose the bias, prefer multi-source claims, let the user see all sources and judge."),
    ("What about patient privacy?",
     "The pipeline doesn't take personal health info — questions are general. If a user submits PHI, it's not stored beyond the cache keyed by SHA256 of the question. A production version would add PII detection before the pipeline."),
    ("Would a doctor endorse this?",
     "Some would say 'useful for patients who insist on googling; not a substitute for consultation.' That's the correct answer, and it's what the disclaimers support."),
    ("What if it gives wrong medical info anyway?",
     "That risk exists. Mitigations: verified citations (Rule 1), verification rate ≥ 90% (Rule 2), no unsafe language (Rule 4), disclaimer present (Rule 5). No system can prove it never errs. This one shows its work so errors are detectable."),
    ("Is there a legal liability concern?",
     "Yes. In the US, software providing medical advice can be regulated as a medical device. The disclaimers ('for research purposes only') are essential, not decorative."),
]

QA_E_MOAT = [
    ("What stops someone copying this?",
     "Nothing technical — the code is open source. What's harder to copy: the eval suite that shows what works and what doesn't, the honest failure documentation, the architecture choices that emerged from debugging real failures. Those are judgment, not code."),
    ("What's your unfair advantage?",
     "Honesty about limitations. Most projects claim 'no bugs.' This one shows a documented 60% baseline, names the failure classes, describes the fixes."),
    ("Could Google or OpenAI just do this?",
     "They could — and are starting to. The realistic path for a project like this is domain-specific, transparent, audit-first. It's not trying to beat Google at search; it's trying to be the version of 'medical AI' that shows its work."),
    ("What's your defensibility over a hackathon project?",
     "Most hackathon projects demo a happy path. This one has: documented failure modes, graceful degradation, auditability, and an eval suite that reruns and measures. That's the difference between a demo and a system."),
    ("If you had to name one thing this project does that nothing else does — what is it?",
     "Shows the governance decision, not just the answer. Per-claim verification verdicts, the 6-rule governance report, the evidence graph, the refusal panel — all in the UI. Most medical AI gives an answer. This gives an auditable answer."),
]

QA_F_COST = [
    ("How much does one query cost?",
     "Free tiers: $0, rate-limited (~200K tokens/day on Groq, ~1500 req/day on Gemini Flash). Paid Groq Dev Tier ($5–10/month): thousands of queries. The pipeline burns ~10–15K tokens per question across 6 agents."),
    ("How does the cache reduce cost?",
     "Repeat questions return cached answers in ~100ms with zero LLM tokens. In testing, cached questions cost ~0.1% of a fresh run. For real traffic with repeated common questions, cache hit rate can exceed 50%, halving effective cost."),
    ("What's the cost of the safety features?",
     "Roughly 15–20% of tokens: the Verifier is the most token-hungry agent (per-claim LLM calls). Critic + Revision add ~10%. This is deliberate — safety is the product, not overhead."),
    ("Where would cost blow up first?",
     "Three places: (1) Verifier on long answers with many claims, (2) full-text scraping of large web pages, (3) OCR on high-resolution images. Mitigations: claim cap (10), source truncation (4K chars), cache."),
    ("Could this run at $0 forever?",
     "Yes, for a demo/portfolio. Groq + Gemini free tiers + Streamlit Cloud free tier + SQLite is $0/month. It fails at scale — rate limits, DB resets, no SLA. But for the stated use case, $0 is honest and sustainable."),
]


# ---------- BUILD PDF ----------
def build_pdf(output_path: Path):
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="MedResearch AI — Complete Project Briefing",
        author="Ayush Nandan",
    )

    story = []

    # ---------- COVER ----------
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("MedResearch AI", styles["CoverTitle"]))
    story.append(Paragraph("Complete Project Briefing", styles["CoverSub"]))
    story.append(Paragraph(
        "Governed Multi-Agent Medical Research System<br/>"
        "English-only v1 · Voice · Image · PDF · Eval Harness",
        styles["CoverSub"]
    ))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(
        f"<b>Author:</b> Ayush Nandan<br/>"
        f"<b>Live:</b> medresearch-ai.streamlit.app<br/>"
        f"<b>Repo:</b> github.com/Ayush-5787/medresearch-ai<br/>"
        f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y')}",
        styles["Body"]
    ))
    story.append(PageBreak())

    # ---------- 1. ELEVATOR PITCH ----------
    story.append(Paragraph("1. Elevator Pitch", styles["H1"]))
    story.append(Paragraph(f"<i>{PITCH}</i>", styles["Quote"]))

    # ---------- 2. WHY THIS PROJECT ----------
    story.append(Paragraph("2. Why This Project?", styles["H1"]))
    story.append(Paragraph(
        "A plain LLM will confidently invent medical facts. In medicine, that's dangerous. "
        "This project asks: what would a medical AI look like if every claim had to be sourced, "
        "verified, and governed — and if the system refused rather than guessed?",
        styles["Body"]
    ))
    t = Table(PROBLEMS, colWidths=[2 * inch, 4.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), CYAN),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GREY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # ---------- 3. STRONG AGENTIC AI ----------
    story.append(Paragraph("3. Why This Is a Strong Agentic AI Project", styles["H1"]))
    for i, line in enumerate([
        "<b>True multi-agent orchestration</b> — 6 agents with distinct roles, passing 17 Pydantic models, not free text.",
        "<b>Real tool use</b> — live PubMed API, Tavily web search, Tesseract OCR, TTS, PDF generation.",
        "<b>A governance layer</b> — rare even in industry demos. Deterministic, auditable safety rules.",
        "<b>Production engineering</b> — auth, caching, rate limiting, multi-provider failover, graceful degradation. Tested live: both LLM providers hit quota mid-run; system degraded honestly instead of crashing.",
        "<b>Honest evaluation</b> — full eval suite (run_evals.py) measures verification rates, not vibes.",
    ], 1):
        story.append(Paragraph(f"{i}. {line}", styles["Body"]))

    story.append(PageBreak())

    # ---------- 4. ARCHITECTURE ----------
    story.append(Paragraph("4. Architecture — 6-Agent Pipeline", styles["H1"]))
    story.append(Paragraph(
        "Question → 🔍 Search → 📖 Reader → ✍️ Writer → 🔎 Critic → 🔧 Revision → ✅ Verifier → 🛡️ Audit Gate → User",
        styles["Quote"]
    ))
    story.append(Spacer(1, 6))
    t = Table(AGENTS, colWidths=[1 * inch, 1.4 * inch, 4.1 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GREY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # ---------- 5. GOVERNANCE ----------
    story.append(Paragraph("5. Governance — 6 Deterministic Rules", styles["H1"]))
    t = Table(GOV_RULES, colWidths=[0.5 * inch, 3 * inch, 1.5 * inch, 1.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), CYAN),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GREY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Decisions:</b> PASS (all pass) · BLOCKED (1–2 non-critical failures, shown with warnings) · "
        "REFUSED (3+ failures or any critical failure — not shown; user gets refusal panel with next steps, "
        "trusted sources, and emergency numbers).",
        styles["Body"]
    ))

    story.append(PageBreak())

    # ---------- 6. TECH STACK ----------
    story.append(Paragraph("6. Technologies Used", styles["H1"]))
    t = Table(TECH_STACK, colWidths=[1.4 * inch, 2.4 * inch, 2.7 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GREY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # ---------- 7. WAR STORIES ----------
    story.append(Paragraph("7. Engineering Highlights", styles["H1"]))
    for line in [
        "<b>Multi-provider failover</b> — When Groq hits a 429, the system fails over to Gemini instantly. Tested live: both providers failed; pipeline still returned an honest structured result instead of crashing.",
        "<b>Cache safety</b> — Failed/empty results are never cached. A cached failure would be served instantly, forever.",
        "<b>Evidence chain fix</b> — Verifier was marking everything NOT_VERIFIED because Reader never passed source text. Fixing data flow took the evidence layer from broken to working.",
        "<b>Rate limiting</b> — llm_delay_seconds = 2 spaces out LLM calls to respect free-tier limits.",
        "<b>Verifier ERROR handling</b> — Verifier crashes recorded as ERROR and excluded from rate, so infra issues don't fake low quality.",
        "<b>Language guard</b> — v1 is English-only; non-English refused in ~300ms with a clear message instead of producing garbage.",
        "<b>Refusal UX</b> — Refusals include 'what you can do,' trusted sources, and country-specific emergency numbers (10 countries).",
    ]:
        story.append(Paragraph(f"• {line}", styles["Body"]))

    story.append(PageBreak())

    # ---------- 8. LIMITATIONS ----------
    story.append(Paragraph("8. Honest Limitations", styles["H1"]))
    for line in [
        "v1 is English-only (multi-language on roadmap).",
        "Verification is LLM-verified against source text — not human-verified.",
        "Free-tier API quotas limit throughput.",
        "Not a medical device — a research tool with disclaimers.",
        "PubMed/web sources have coverage gaps; some claims genuinely can't be verified, and the system correctly refuses those.",
    ]:
        story.append(Paragraph(f"• {line}", styles["Body"]))
    story.append(Spacer(1, 10))

    # ---------- 9. FUTURE ----------
    story.append(Paragraph("9. Future Plans", styles["H1"]))
    for line in [
        "Multi-language retrieval (UI reserves architecture).",
        "Retrieval-based verification against freshly retrieved evidence.",
        "More providers — OpenRouter, local models (Ollama) for zero-cost fallback.",
        "Clinical guidelines integration (WHO/NIH/CDC) as a first-class source tier.",
        "Human-in-the-loop expert review for low-confidence answers.",
        "Feedback loop — user ratings feeding the eval suite.",
        "Fine-tuned verifier — a small medical NLI model instead of a general LLM.",
        "Monitoring dashboard — refusal rates, verification rates, provider health.",
    ]:
        story.append(Paragraph(f"• {line}", styles["Body"]))

    story.append(PageBreak())

    # ---------- 10. Q&A BANK ----------
    story.append(Paragraph("10. Teacher Q&A Bank — 70 Questions", styles["H1"]))
    story.append(Paragraph(
        "Organized by category. Practice these aloud before the viva.",
        styles["Body"]
    ))
    story.append(Spacer(1, 10))

    sections = [
        ("A. Trust & Comparison vs ChatGPT / Gemini / Other AI", QA_A_TRUST),
        ("B. Data & Datasets", QA_B_DATA),
        ("C. Business & Impact", QA_C_BUSINESS),
        ("D. Ethics & Compliance", QA_D_ETHICS),
        ("E. Competitive & Moat", QA_E_MOAT),
        ("F. Cost & Economics", QA_F_COST),
    ]

    for section_title, qa_list in sections:
        story.append(Paragraph(section_title, styles["H2"]))
        for i, (q, a) in enumerate(qa_list, 1):
            story.append(KeepTogether([
                Paragraph(f"Q. {q}", styles["Q"]),
                Paragraph(f"A. {a}", styles["A"]),
            ]))

    # ---------- FOOTER NOTE ----------
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "<i>Note: The original 30 questions (Basic, Medium, Advanced) remain in the "
        "master briefing document. This PDF extends them with 40 new questions "
        "across Trust, Data, Business, Ethics, Moat, and Cost.</i>",
        styles["Body"]
    ))

    doc.build(story)
    print(f"[OK] PDF generated: {output_path}")
    print(f"[OK] Size: {output_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    out = Path(__file__).parent / "MedResearch_AI_Briefing.pdf"
    build_pdf(out)