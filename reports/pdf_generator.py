"""
MedResearch AI — PDF Report Generator (reportlab version)
Creates professional PDF research reports from FinalResult.
"""

from datetime import datetime
from io import BytesIO
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.enums import TA_LEFT

from core.schemas import FinalResult, AuditReport


class PDFReportGenerator:
    """Generates PDF reports from research results using reportlab."""

    def generate(
        self,
        result: FinalResult,
        audit_report: AuditReport,
        language: str = "en",
        country: str = "DEFAULT",
    ) -> bytes:
        """Generate PDF report."""
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm,
                title="MedResearch AI Report",
                author="MedResearch AI",
            )

            styles = self._get_styles()
            story = []

            # Header
            story.extend(self._build_header(result, language, country, styles))
            story.append(Spacer(1, 0.5*cm))

            # Question
            story.append(Paragraph("Question", styles["H2"]))
            story.append(Paragraph(self._escape(result.question), styles["Body"]))
            story.append(Spacer(1, 0.5*cm))

            # Summary metrics
            story.extend(self._build_metrics(result, audit_report, styles))
            story.append(Spacer(1, 0.5*cm))

            # Answer
            story.append(Paragraph("Answer", styles["H2"]))
            story.append(Paragraph(self._escape(result.answer), styles["Body"]))
            story.append(Spacer(1, 0.5*cm))

            # Verification report
            if result.verification:
                story.append(PageBreak())
                story.extend(self._build_verification(result, styles))
                story.append(Spacer(1, 0.5*cm))

            # Governance report
            story.extend(self._build_governance(audit_report, styles))
            story.append(Spacer(1, 0.5*cm))

            # Sources
            story.append(PageBreak())
            story.extend(self._build_sources(result, styles))
            story.append(Spacer(1, 0.5*cm))

            # Disclaimer
            story.extend(self._build_disclaimer(result, styles))

            doc.build(story)
            buffer.seek(0)
            return buffer.read()

        except Exception as e:
            print(f"[PDFGenerator] Error: {e}")
            import traceback
            traceback.print_exc()
            return b""

    def _get_styles(self):
        """Define PDF styles."""
        styles = getSampleStyleSheet()

        styles.add(ParagraphStyle(
            name="Title1",
            parent=styles["Title"],
            fontSize=22,
            textColor=colors.HexColor("#0066cc"),
            spaceAfter=6,
        ))

        styles.add(ParagraphStyle(
            name="H2",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#0066cc"),
            spaceBefore=12,
            spaceAfter=6,
            borderColor=colors.HexColor("#0066cc"),
            borderWidth=0,
            borderPadding=0,
        ))

        styles.add(ParagraphStyle(
            name="H3",
            parent=styles["Heading3"],
            fontSize=11,
            textColor=colors.HexColor("#333333"),
            spaceBefore=8,
            spaceAfter=4,
        ))

        styles.add(ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontSize=10,
            leading=15,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#222222"),
        ))

        styles.add(ParagraphStyle(
            name="Meta",
            parent=styles["BodyText"],
            fontSize=9,
            textColor=colors.HexColor("#666666"),
        ))

        styles.add(ParagraphStyle(
            name="SmallMono",
            parent=styles["BodyText"],
            fontSize=8,
            fontName="Courier",
            textColor=colors.HexColor("#444444"),
        ))

        return styles

    def _escape(self, text: str) -> str:
        """Escape special characters for reportlab Paragraph."""
        if not text:
            return ""
        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )

    def _build_header(self, result, language, country, styles):
        """Build the report header."""
        elements = []
        elements.append(Paragraph("MedResearch AI Report", styles["Title1"]))

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Paragraph(
            f"<b>Generated:</b> {ts} &nbsp; | &nbsp; "
            f"<b>Language:</b> {language} &nbsp; | &nbsp; "
            f"<b>Country:</b> {country}",
            styles["Meta"]
        ))
        report_id = f"MRAI-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        elements.append(Paragraph(f"<b>Report ID:</b> {report_id}", styles["Meta"]))
        return elements

    def _build_metrics(self, result, audit, styles):
        """Build metrics summary table."""
        vc = result.verification.verified_count if result.verification else 0
        vt = result.verification.total_claims if result.verification else 0

        data = [
            ["Confidence", "Verified", "Rules Passed", "Status", "Time"],
            [
                f"{result.confidence:.2f}",
                f"{vc}/{vt}",
                f"{audit.rules_passed}/6",
                result.status,
                f"{result.total_duration_ms // 1000}s",
            ]
        ]

        table = Table(data, colWidths=[3*cm]*5)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0066cc")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, 1), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f0f7ff")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))

        return [table]

    def _build_verification(self, result, styles):
        """Build verification section."""
        elements = [Paragraph("Verification Report", styles["H2"])]
        v = result.verification

        elements.append(Paragraph(
            f"Total claims: <b>{v.total_claims}</b> &nbsp; | &nbsp; "
            f"Verified: <b>{v.verified_count}</b> &nbsp; | &nbsp; "
            f"Rate: <b>{v.verification_rate:.0%}</b>",
            styles["Body"]
        ))

        for res in v.results[:10]:
            icon = {
                "VERIFIED": "[OK]",
                "PARTIALLY_VERIFIED": "[PART]",
                "NOT_VERIFIED": "[NO]",
                "CONTRADICTED": "[X]",
            }.get(res.verdict, "[?]")

            claim_text = (res.claim_text or "")[:200]
            evidence = (res.evidence or "")[:200]
            url = (res.source_url or "")[:80]

            elements.append(Paragraph(
                f"<b>{icon} Claim {res.claim_index + 1}:</b> {self._escape(claim_text)}",
                styles["Body"]
            ))
            elements.append(Paragraph(
                f"Verdict: <b>{res.verdict}</b> ({res.confidence:.2f})",
                styles["Meta"]
            ))
            if url:
                elements.append(Paragraph(f"Source: {self._escape(url)}", styles["Meta"]))
            if evidence:
                elements.append(Paragraph(
                    f"<i>Evidence: {self._escape(evidence)}</i>",
                    styles["Meta"]
                ))
            elements.append(Spacer(1, 0.2*cm))

        return elements

    def _build_governance(self, audit, styles):
        """Build governance section."""
        elements = [Paragraph("Governance Report", styles["H2"])]
        elements.append(Paragraph(
            f"<b>Decision:</b> {audit.decision} — {self._escape(audit.reasoning)}",
            styles["Body"]
        ))
        elements.append(Spacer(1, 0.3*cm))

        data = [["Rule", "Status", "Actual", "Threshold"]]
        for rule in audit.rules:
            status = "PASS" if rule.passed else "FAIL"
            data.append([
                f"{rule.rule_id}: {rule.name}",
                status,
                rule.actual_value[:40],
                rule.threshold[:30],
            ])

        table = Table(data, colWidths=[6*cm, 2*cm, 4*cm, 4*cm])
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0066cc")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        for i, rule in enumerate(audit.rules, 1):
            if rule.passed:
                style.append(("TEXTCOLOR", (1, i), (1, i), colors.HexColor("#228b22")))
            else:
                style.append(("TEXTCOLOR", (1, i), (1, i), colors.HexColor("#cc0000")))
        table.setStyle(TableStyle(style))

        elements.append(table)
        return elements

    def _build_sources(self, result, styles):
        """Build sources section."""
        elements = [Paragraph("Sources & References", styles["H2"])]
        for i, source in enumerate(result.sources[:15], 1):
            title = (source.title or f"Source {i}")[:80]
            elements.append(Paragraph(
                f"<b>[{i}]</b> {self._escape(title)}",
                styles["Body"]
            ))
            elements.append(Paragraph(
                f"{self._escape(source.url)}",
                styles["SmallMono"]
            ))
            elements.append(Paragraph(
                f"Type: {source.source_type} | Credibility: {source.credibility_score:.2f}",
                styles["Meta"]
            ))
            elements.append(Spacer(1, 0.2*cm))
        return elements

    def _build_disclaimer(self, result, styles):
        """Build disclaimer."""
        elements = [Spacer(1, 0.5*cm)]
        elements.append(Paragraph("Medical Disclaimer", styles["H2"]))
        elements.append(Paragraph(
            f"⚠️ {self._escape(result.disclaimer)}",
            styles["Body"]
        ))
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph(
            "Generated by MedResearch AI — Governed Multi-Agent Research System",
            styles["Meta"]
        ))
        elements.append(Paragraph(
            "github.com/Ayush-5787/medresearch-ai",
            styles["Meta"]
        ))
        return elements


print("[pdf_generator] PDFReportGenerator loaded (reportlab)")