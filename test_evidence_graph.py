"""
MedResearch AI — Test Evidence Graph
Runs full pipeline and builds the evidence graph.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.orchestrator import MedResearchPipeline
from governance.audit_gate import AuditGate
from governance.evidence_graph import EvidenceGraphBuilder


async def main():
    print("=" * 60)
    print("TESTING EVIDENCE GRAPH")
    print("=" * 60)
    print()

    # Run pipeline
    pipeline = MedResearchPipeline()
    question = "What are the side effects of metformin?"
    result = await pipeline.run(question, verbose=True)

    # Run audit gate (governance check)
    print("\n" + "=" * 60)
    print("AUDIT GATE")
    print("=" * 60)
    audit_gate = AuditGate()
    audit_report = audit_gate.evaluate(result)
    print(f"\n  Decision: {audit_report.decision}")
    print(f"  Rules passed: {audit_report.rules_passed}/{len(audit_report.rules)}")

    # Build evidence graph
    print("\n" + "=" * 60)
    print("EVIDENCE GRAPH")
    print("=" * 60)
    builder = EvidenceGraphBuilder()
    graph = builder.build(result)

    # Display stats
    print("\nGRAPH STATS:")
    for k, v in graph.stats.items():
        print(f"  {k}: {v}")

    # Display nodes summary
    print(f"\nNODES ({len(graph.nodes)}):")
    claims = [n for n in graph.nodes if n.type == "claim"]
    sources = [n for n in graph.nodes if n.type == "source"]
    print(f"  Claims:  {len(claims)}")
    print(f"  Sources: {len(sources)}")

    print(f"\nSample claims (first 3):")
    for c in claims[:3]:
        print(f"  [{c.id}] {c.text[:70]}... (confidence={c.confidence:.2f})")

    print(f"\nSample sources (first 3):")
    for s in sources[:3]:
        print(f"  [{s.id}] {s.label[:60]} ({s.source_type})")
        print(f"        {s.url[:80]}")

    # Display edges
    print(f"\nEDGES ({len(graph.edges)}):")
    print("  Sample edges (first 5):")
    for e in graph.edges[:5]:
        icon = "[OK]" if e.verified else "[--]"
        print(f"  {icon} {e.source_id} → {e.target_id} ({e.relationship})")

    # D3 export
    print("\n" + "=" * 60)
    print("D3.JS EXPORT (for visualization)")
    print("=" * 60)
    d3_data = builder.to_d3_format(graph)

    # Save to file for UI to use
    output_path = Path("evidence_graph.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(d3_data, f, indent=2, ensure_ascii=False)

    print(f"\n  D3 data saved to: {output_path}")
    print(f"  Nodes: {len(d3_data['nodes'])}")
    print(f"  Links: {len(d3_data['links'])}")
    print(f"\n  File size: {output_path.stat().st_size} bytes")

    # Preview the JSON
    print("\nJSON PREVIEW (first 3 nodes):")
    print(json.dumps(d3_data["nodes"][:3], indent=2)[:800])

    print("\n" + "=" * 60)
    print("EVIDENCE GRAPH TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())