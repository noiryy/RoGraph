"""Small, read-only adapters from MCP tools to the persisted graph."""

from __future__ import annotations

from typing import Any

from roblox_graph.graph.engine import GraphEngine
from roblox_graph.models.edge import Edge
from roblox_graph.models.node import Node
from roblox_graph.storage.repositories import GraphRepository


class GraphTools:
    """Expose compact, stable graph payloads without giving tools write access."""

    def __init__(self, repository: GraphRepository) -> None:
        self.repository = repository
        self.graph = GraphEngine(repository)

    def search_project(self, project_id: str, query: str, limit: int = 20) -> dict[str, object]:
        return {
            "query": query,
            "results": self._nodes(self.graph.search_project(project_id, query, limit=limit)),
        }

    def get_node(self, node_id: str) -> dict[str, object]:
        return {"node": self._node_or_none(self.graph.get_node(node_id))}

    def get_script(self, node_id: str) -> dict[str, object]:
        node = self.graph.get_node(node_id)
        if node is None:
            return {"node": None, "source": None}
        return {"node": self._node(node), "source": node.source}

    def get_dependencies(self, node_id: str, depth: int = 1) -> dict[str, object]:
        return {
            "node": self._node_or_none(self.graph.get_node(node_id)),
            "dependencies": self._nodes(self.graph.get_dependencies(node_id, depth=depth)),
        }

    def get_dependents(self, node_id: str, depth: int = 1) -> dict[str, object]:
        return {
            "node": self._node_or_none(self.graph.get_node(node_id)),
            "dependents": self._nodes(self.graph.get_dependents(node_id, depth=depth)),
        }

    def get_related(self, node_id: str, limit: int = 25) -> dict[str, object]:
        return {
            "node": self._node_or_none(self.graph.get_node(node_id)),
            "related": self._nodes(self.graph.get_related(node_id, limit=limit)),
        }

    def get_subgraph(self, node_id: str, depth: int = 1) -> dict[str, object]:
        nodes, edges = self.graph.get_subgraph(node_id, depth=depth)
        return {"nodes": self._nodes(nodes), "edges": [self._edge(edge) for edge in edges]}

    def trace_path(self, source_id: str, target_id: str) -> dict[str, object]:
        return {"path": self._nodes(self.graph.shortest_path(source_id, target_id))}

    def find_remote_usage(self, project_id: str, name: str | None = None) -> dict[str, object]:
        return self._find_usage(project_id, {"RemoteEvent", "RemoteFunction"}, name)

    def find_datastore_usage(self, project_id: str, name: str | None = None) -> dict[str, object]:
        return self._find_usage(project_id, {"DataStore", "OrderedDataStore"}, name)

    def find_tag_usage(self, project_id: str, name: str | None = None) -> dict[str, object]:
        return self._find_usage(project_id, {"CollectionServiceTag"}, name)

    def find_attribute_usage(self, project_id: str, name: str | None = None) -> dict[str, object]:
        return self._find_usage(project_id, {"Attribute"}, name)

    def get_project_overview(self, project_id: str) -> dict[str, object]:
        nodes = self.repository.list_nodes(project_id)
        edges = self.repository.list_edges(project_id)
        counts: dict[str, int] = {}
        for node in nodes:
            counts[node.type] = counts.get(node.type, 0) + 1
        return {
            "project_id": project_id,
            "nodes": len(nodes),
            "edges": len(edges),
            "node_types": dict(sorted(counts.items())),
        }

    def get_god_nodes(self, project_id: str, limit: int = 10) -> dict[str, object]:
        nodes = self.repository.list_nodes(project_id)
        ranked = sorted(nodes, key=lambda node: (-self.graph.degree(node.id), node.name, node.id))
        return {
            "nodes": [
                self._node(node) | {"degree": self.graph.degree(node.id)}
                for node in ranked[:limit]
            ]
        }

    def _find_usage(
        self, project_id: str, node_types: set[str], name: str | None
    ) -> dict[str, object]:
        matching = [
            node
            for node in self.repository.list_nodes(project_id)
            if node.type in node_types and (name is None or name.lower() in node.name.lower())
        ]
        return {
            "targets": [
                {
                    "node": self._node(node),
                    "usages": [
                        self._edge(edge)
                        for edge in self.repository.list_incident_edges(node.id)
                        if edge.target_id == node.id and edge.type != "CONTAINS"
                    ],
                }
                for node in matching
            ]
        }

    @staticmethod
    def _node(node: Node) -> dict[str, Any]:
        return node.model_dump(mode="json")

    def _node_or_none(self, node: Node | None) -> dict[str, Any] | None:
        return self._node(node) if node else None

    def _nodes(self, nodes: list[Node]) -> list[dict[str, Any]]:
        return [self._node(node) for node in nodes]

    @staticmethod
    def _edge(edge: Edge) -> dict[str, Any]:
        return edge.model_dump(mode="json")

