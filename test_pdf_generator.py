"""
MedResearch AI — Test PDF Report Generator
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.orchestrator import MedResearchPipeline
from governance.audit_gate import AuditGate
from reports.pdf_generator import PDFReportGenerator


async def main():
    print("=" * 60)
    print("TESTING PDF REPORT GENERATOR")
    print("=" * 60)

    # Run pipeline
    print("\nRunning pipeline (this takes ~2-3 minutes)...\n")
    pipeline = MedResearchPipeline()
    result = await pipeline.run(
        "What are the side effects of metformin?",
        language="en",
        country="IN",
        verbose=False,
    )

    # Run audit gate
    audit_gate = AuditGate()
    audit_report = audit_gate.evaluate(result)

    print(f"\nPipeline complete:")
    print(f"  Status: {result.status}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Verified: {result.verification.verified_count}/{result.verification.total_claims}")

    # Generate PDF
    print("\nGenerating PDF...")
    gen = PDFReportGenerator()
    pdf_bytes = gen.generate(result, audit_report, language="en", country="IN")

    if pdf_bytes:
        output_path = Path("test_report.pdf")
        output_path.write_bytes(pdf_bytes)
        print(f"✅ PDF generated: {len(pdf_bytes)} bytes")
        print(f"   Saved to: {output_path.absolute()}")
        print(f"\n   Open with: start test_report.pdf")
    else:
        print("❌ Failed to generate PDF")

    print("\n" + "=" * 60)
    print("PDF TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())