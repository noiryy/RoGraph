"""Deterministic, dependency-free graph centrality and coupling metrics."""

from __future__ import annotations

from dataclasses import dataclass

from roblox_graph.models.edge import Edge
from roblox_graph.models.node import Node

EDGE_WEIGHTS = {
    "REQUIRES": 3.0,
    "FIRES": 3.0,
    "INVOKES": 3.0,
    "LISTENS_TO": 3.0,
    "READS": 2.5,
    "WRITES": 2.5,
    "USES_SERVICE": 2.0,
    "USES_TAG": 2.0,
    "READS_ATTRIBUTE": 2.0,
    "WRITES_ATTRIBUTE": 2.0,
    "REFERENCES": 1.0,
    "CONTAINS": 0.25,
}


@dataclass(frozen=True, slots=True)
class NodeMetrics:
    node_id: str
    degree: int
    incoming_degree: int
    outgoing_degree: int
    weighted_degree: float
    coupling_score: float


def calculate_metrics(nodes: list[Node], edges: list[Edge]) -> dict[str, NodeMetrics]:
    """Calculate simple explainable metrics without a third-party graph dependency."""
    incoming = {node.id: 0 for node in nodes}
    outgoing = {node.id: 0 for node in nodes}
    weighted = {node.id: 0.0 for node in nodes}
    neighbor_types: dict[str, set[str]] = {node.id: set() for node in nodes}
    for edge in edges:
        if edge.source_id not in incoming or edge.target_id not in incoming:
            continue
        weight = EDGE_WEIGHTS.get(edge.type, 1.0)
        outgoing[edge.source_id] += 1
        incoming[edge.target_id] += 1
        weighted[edge.source_id] += weight
        weighted[edge.target_id] += weight
        neighbor_types[edge.source_id].add(edge.type)
        neighbor_types[edge.target_id].add(edge.type)
    return {
        node_id: NodeMetrics(
            node_id=node_id,
            degree=incoming[node_id] + outgoing[node_id],
            incoming_degree=incoming[node_id],
            outgoing_degree=outgoing[node_id],
            weighted_degree=round(weighted[node_id], 2),
            coupling_score=round(
                weighted[node_id] + len(neighbor_types[node_id]) * 0.5,
                2,
            ),
        )
        for node_id in incoming
    }
