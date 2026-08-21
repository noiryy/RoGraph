"""Traversal and metric operations over the persisted directed graph."""

from __future__ import annotations

from collections import deque

from roblox_graph.models.edge import Edge
from roblox_graph.models.node import Node
from roblox_graph.storage.repositories import GraphRepository


class GraphEngine:
    def __init__(self, repository: GraphRepository) -> None:
        self.repository = repository

    def get_node(self, node_id: str) -> Node | None:
        return self.repository.get_node(node_id)

    def get_neighbors(self, node_id: str, *, direction: str = "both") -> list[Node]:
        if direction not in {"incoming", "outgoing", "both"}:
            raise ValueError("direction must be incoming, outgoing, or both")
        neighbor_ids: set[str] = set()
        for edge in self.repository.list_incident_edges(node_id):
            if direction in {"outgoing", "both"} and edge.source_id == node_id:
                neighbor_ids.add(edge.target_id)
            if direction in {"incoming", "both"} and edge.target_id == node_id:
                neighbor_ids.add(edge.source_id)
        return [node for candidate in sorted(neighbor_ids) if (node := self.get_node(candidate))]

    def get_dependencies(self, node_id: str, *, depth: int = 1) -> list[Node]:
        return self._traverse(node_id, direction="outgoing", depth=depth)

    def get_dependents(self, node_id: str, *, depth: int = 1) -> list[Node]:
        return self._traverse(node_id, direction="incoming", depth=depth)

    def search_project(self, project_id: str, query: str, *, limit: int = 20) -> list[Node]:
        if not query.strip():
            return []
        return self.repository.search_nodes(project_id, query.strip(), limit=max(1, limit))

    def get_related(self, node_id: str, *, limit: int = 25) -> list[Node]:
        """Return direct neighbors ranked by relationship strength and degree."""
        weights = {
            "REQUIRES": 3,
            "USES_DATASTORE": 3,
            "INVOKES": 3,
            "CALLS": 2,
            "FIRES": 2,
            "LISTENS_TO": 2,
            "REFERENCES": 1,
            "CONTAINS": 1,
        }
        scores: dict[str, int] = {}
        for edge in self.repository.list_incident_edges(node_id):
            other = edge.target_id if edge.source_id == node_id else edge.source_id
            scores[other] = scores.get(other, 0) + weights.get(edge.type, 1)
        ranked = sorted(
            scores,
            key=lambda candidate: (-scores[candidate], -self.degree(candidate), candidate),
        )
        return [node for candidate in ranked[:limit] if (node := self.get_node(candidate))]

    def get_subgraph(self, node_id: str, *, depth: int = 1) -> tuple[list[Node], list[Edge]]:
        nodes = [self.get_node(node_id)] + self._traverse(node_id, direction="both", depth=depth)
        selected = {node.id for node in nodes if node}
        project_id = next((node.project_id for node in nodes if node), None)
        edges = (
            []
            if project_id is None
            else [
                edge
                for edge in self.repository.list_edges(project_id)
                if edge.source_id in selected and edge.target_id in selected
            ]
        )
        return [node for node in nodes if node], edges

    def shortest_path(self, source_id: str, target_id: str) -> list[Node]:
        if not self.get_node(source_id) or not self.get_node(target_id):
            return []
        queue: deque[list[str]] = deque([[source_id]])
        visited = {source_id}
        while queue:
            path = queue.popleft()
            current = path[-1]
            if current == target_id:
                return [node for item in path if (node := self.get_node(item))]
            for neighbor in self.get_neighbors(current, direction="outgoing"):
                if neighbor.id not in visited:
                    visited.add(neighbor.id)
                    queue.append([*path, neighbor.id])
        return []

    def degree(self, node_id: str) -> int:
        return len(self.repository.list_incident_edges(node_id))

    def incoming_degree(self, node_id: str) -> int:
        return sum(
            edge.target_id == node_id for edge in self.repository.list_incident_edges(node_id)
        )

    def outgoing_degree(self, node_id: str) -> int:
        return sum(
            edge.source_id == node_id for edge in self.repository.list_incident_edges(node_id)
        )

    def _traverse(self, node_id: str, *, direction: str, depth: int) -> list[Node]:
        if depth < 1:
            return []
        visited = {node_id}
        queue: deque[tuple[str, int]] = deque([(node_id, 0)])
        results: list[Node] = []
        while queue:
            current, distance = queue.popleft()
            if distance == depth:
                continue
            for neighbor in self.get_neighbors(current, direction=direction):
                if neighbor.id not in visited:
                    visited.add(neighbor.id)
                    results.append(neighbor)
                    queue.append((neighbor.id, distance + 1))
        return results
