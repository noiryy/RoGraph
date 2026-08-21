"""Project-level architectural summaries derived from the persisted graph."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from roblox_graph.graph.communities import find_communities
from roblox_graph.graph.metrics import NodeMetrics, calculate_metrics
from roblox_graph.models.edge import Edge
from roblox_graph.models.node import Node
from roblox_graph.storage.repositories import GraphRepository


class GraphIntelligence:
    """Compute explainable architecture signals on demand for a local project."""

    def __init__(self, repository: GraphRepository) -> None:
        self.repository = repository

    def overview(self, project_id: str) -> dict[str, Any]:
        nodes, edges, metrics, communities = self._project_data(project_id)
        groups: dict[str, list[Node]] = defaultdict(list)
        for node in nodes:
            groups[communities[node.id]].append(node)
        connected_groups = {
            community_id: members
            for community_id, members in groups.items()
            if len(members) > 1
        }
        areas = [
            self._area_summary(community_id, members, edges, metrics)
            for community_id, members in connected_groups.items()
        ]
        areas.sort(key=lambda area: (-area["node_count"], area["id"]))
        node_types = Counter(node.type for node in nodes)
        edge_types = Counter(edge.type for edge in edges)
        god_nodes = self._ranked_nodes(nodes, metrics, 5)
        connected_node_count = sum(len(members) for members in connected_groups.values())
        return {
            "project_id": project_id,
            "nodes": len(nodes),
            "edges": len(edges),
            "node_types": dict(sorted(node_types.items())),
            "edge_types": dict(sorted(edge_types.items())),
            "community_count": len(connected_groups),
            "isolated_node_count": len(nodes) - connected_node_count,
            "architecture_areas": areas[:8],
            "coupling_indicators": god_nodes,
        }

    def god_nodes(self, project_id: str, *, limit: int = 10) -> list[dict[str, Any]]:
        nodes, _, metrics, _ = self._project_data(project_id)
        return self._ranked_nodes(nodes, metrics, limit)

    def _project_data(
        self, project_id: str
    ) -> tuple[list[Node], list[Edge], dict[str, NodeMetrics], dict[str, str]]:
        nodes = self.repository.list_nodes(project_id)
        edges = self.repository.list_edges(project_id)
        return nodes, edges, calculate_metrics(nodes, edges), find_communities(nodes, edges)

    @staticmethod
    def _ranked_nodes(
        nodes: list[Node], metrics: dict[str, NodeMetrics], limit: int
    ) -> list[dict[str, Any]]:
        ranked = sorted(
            nodes,
            key=lambda node: (
                -metrics[node.id].coupling_score,
                -metrics[node.id].weighted_degree,
                node.name,
                node.id,
            ),
        )
        return [
            node.model_dump(mode="json")
            | {
                "degree": metrics[node.id].degree,
                "incoming_degree": metrics[node.id].incoming_degree,
                "outgoing_degree": metrics[node.id].outgoing_degree,
                "weighted_degree": metrics[node.id].weighted_degree,
                "coupling_score": metrics[node.id].coupling_score,
            }
            for node in ranked[: max(1, min(limit, 100))]
        ]

    @staticmethod
    def _area_summary(
        community_id: str,
        members: list[Node],
        edges: list[Edge],
        metrics: dict[str, NodeMetrics],
    ) -> dict[str, Any]:
        member_ids = {node.id for node in members}
        relationships = sum(
            edge.type != "CONTAINS"
            and edge.source_id in member_ids
            and edge.target_id in member_ids
            for edge in edges
        )
        representative = GraphIntelligence._ranked_nodes(members, metrics, 1)[0]
        return {
            "id": community_id,
            "node_count": len(members),
            "relationship_count": relationships,
            "node_types": dict(sorted(Counter(node.type for node in members).items())),
            "representative": representative,
        }
