"""
MedResearch AI — Evidence Graph Builder
Creates a graph data structure that links claims to their sources.

Used by:
- Streamlit UI (Step 12) for interactive visualization
- Compliance reports (audit trail)
- Debugging (see which sources support which claims)
"""

from typing import List
from core.schemas import (
    FinalResult,
    GraphNode,
    GraphEdge,
    EvidenceGraph,
)


class EvidenceGraphBuilder:
    """
    Builds an evidence graph from a FinalResult.
    Nodes = claims + sources
    Edges = "claim X is supported by source Y"
    """

    def build(self, result: FinalResult) -> EvidenceGraph:
        """Build the evidence graph from a pipeline result."""
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []

        # Create claim nodes
        claim_id_map = {}  # claim index → node id
        for i, claim in enumerate(result.claims):
            node_id = f"claim_{i+1}"
            claim_id_map[i] = node_id
            nodes.append(GraphNode(
                id=node_id,
                type="claim",
                label=f"Claim {i+1}",
                text=claim.text,
                confidence=claim.confidence,
                verified=claim.verified,
            ))

        # Create source nodes
        source_id_map = {}  # url → node id
        for i, source in enumerate(result.sources):
            node_id = f"source_{i+1}"
            source_id_map[source.url] = node_id
            nodes.append(GraphNode(
                id=node_id,
                type="source",
                label=source.title[:60] if source.title else f"Source {i+1}",
                url=source.url,
                source_type=source.source_type,
                credibility_score=source.credibility_score,
            ))

        # Create edges (claim → source)
        for i, claim in enumerate(result.claims):
            claim_id = claim_id_map[i]
            for url in claim.source_urls:
                source_id = source_id_map.get(url)
                if source_id:
                    edges.append(GraphEdge(
                        source_id=claim_id,
                        target_id=source_id,
                        relationship="supported_by",
                        verified=claim.verified,
                    ))

        # Compute stats
        stats = self._compute_stats(nodes, edges, result)

        return EvidenceGraph(
            nodes=nodes,
            edges=edges,
            stats=stats,
        )

    def _compute_stats(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        result: FinalResult,
    ) -> dict:
        """Compute statistics about the graph."""
        claims = [n for n in nodes if n.type == "claim"]
        sources = [n for n in nodes if n.type == "source"]

        # Average citations per claim
        cites_per_claim = {}
        for e in edges:
            cites_per_claim[e.source_id] = cites_per_claim.get(e.source_id, 0) + 1
        avg_cites = (
            sum(cites_per_claim.values()) / len(claims) if claims else 0.0
        )

        # Average claims per source
        claims_per_source = {}
        for e in edges:
            claims_per_source[e.target_id] = claims_per_source.get(e.target_id, 0) + 1
        avg_claims_per_source = (
            sum(claims_per_source.values()) / len(sources) if sources else 0.0
        )

        # Verification stats
        verified_edges = sum(1 for e in edges if e.verified)

        return {
            "total_claims": len(claims),
            "total_sources": len(sources),
            "total_edges": len(edges),
            "avg_citations_per_claim": round(avg_cites, 2),
            "avg_claims_per_source": round(avg_claims_per_source, 2),
            "verified_edges": verified_edges,
            "verification_rate": (
                round(verified_edges / len(edges), 3) if edges else 0.0
            ),
            "answer_length": len(result.answer),
            "overall_confidence": result.confidence,
            "status": result.status,
        }

    def to_d3_format(self, graph: EvidenceGraph) -> dict:
        """
        Convert to D3.js-friendly format for visualization.
        D3 expects: {nodes: [...], links: [...]}
        """
        return {
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "label": n.label,
                    "text": n.text if n.type == "claim" else "",
                    "url": n.url if n.type == "source" else "",
                    "confidence": n.confidence if n.type == "claim" else n.credibility_score,
                    "verified": n.verified if n.type == "claim" else False,
                }
                for n in graph.nodes
            ],
            "links": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "relationship": e.relationship,
                    "verified": e.verified,
                }
                for e in graph.edges
            ],
            "stats": graph.stats,
        }


print("[evidence_graph] EvidenceGraphBuilder loaded")