"""Translate Roblox Studio snapshots into the canonical graph domain."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass

from roblox_graph.analysis.runner import AnalyzerRunner
from roblox_graph.models.edge import Edge
from roblox_graph.models.node import Node
from roblox_graph.models.project import Project
from roblox_graph.models.studio import StudioEvent, StudioInstance, StudioSnapshot
from roblox_graph.storage.repositories import GraphRepository

_TYPE_BY_CLASS_NAME = {
    "Script": "Script",
    "LocalScript": "LocalScript",
    "ModuleScript": "ModuleScript",
    "RemoteEvent": "RemoteEvent",
    "RemoteFunction": "RemoteFunction",
    "BindableEvent": "BindableEvent",
    "BindableFunction": "BindableFunction",
    "Folder": "Folder",
    "Model": "Model",
}


@dataclass(frozen=True, slots=True)
class IngestionResult:
    project: Project
    nodes: list[Node]
    edges: list[Edge]
    warnings: list[str]


@dataclass(frozen=True, slots=True)
class EventResult:
    project_id: str
    event_type: str
    warnings: list[str]


class StudioIngestionService:
    """Ingest full snapshots; incremental events are intentionally a later phase."""

    def __init__(
        self, repository: GraphRepository, analyzers: AnalyzerRunner | None = None
    ) -> None:
        self.repository = repository
        self.analyzers = analyzers or AnalyzerRunner()
        self._recently_removed: dict[tuple[str, str], float] = {}

    def ingest_snapshot(self, snapshot: StudioSnapshot) -> IngestionResult:
        project = Project(
            id=snapshot.project.id,
            name=snapshot.project.name,
            place_id=snapshot.project.place_id,
        )
        place = Node.create(
            project_id=project.id,
            type="Place",
            name=project.name,
            path="game",
            metadata={"place_id": project.place_id} if project.place_id else {},
        )
        nodes = [place]
        paths = {"game": place}

        for instance in snapshot.instances:
            if not self._is_architectural(instance):
                continue
            node = self._to_node(project.id, instance)
            nodes.append(node)
            paths[instance.path] = node

        edges: list[Edge] = []
        for instance in snapshot.instances:
            snapshot_node = paths.get(instance.path)
            if snapshot_node is None:
                continue
            parent = paths.get(instance.parent_path or "game")
            if parent is not None and parent.id != snapshot_node.id:
                edges.append(
                    Edge.create(
                        project_id=project.id,
                        source_id=parent.id,
                        target_id=snapshot_node.id,
                        type="CONTAINS",
                        metadata={"origin": "studio_snapshot"},
                    )
                )

        analysis = self.analyzers.analyze_scripts(project.id, nodes)
        nodes = self._deduplicate_nodes([*nodes, *analysis.nodes])
        edges = self._deduplicate_edges([*edges, *analysis.edges])
        self.repository.replace_project_graph(project, nodes, edges)
        return IngestionResult(
            project=project,
            nodes=nodes,
            edges=edges,
            warnings=analysis.warnings,
        )

    def ingest_event(self, event: StudioEvent) -> EventResult:
        if event.kind == "remove":
            path = event.path or ""
            self._recently_removed[(event.project_id, path)] = time.monotonic()
            removed = self.repository.remove_node_at_path(event.project_id, path)
            return EventResult(
                project_id=event.project_id,
                event_type="node_removed" if removed else "node_unchanged",
                warnings=[],
            )

        instance = event.instance
        assert instance is not None
        if self._was_just_removed(event.project_id, instance.path):
            return EventResult(event.project_id, "node_unchanged", [])
        if not self._is_architectural(instance):
            self.repository.remove_node_at_path(event.project_id, instance.path)
            return EventResult(event.project_id, "node_removed", [])
        node = self._to_node(event.project_id, instance)
        current_nodes = self.repository.list_nodes(event.project_id)
        current_by_path = {value.path: value for value in current_nodes if value.path}
        current_by_path[instance.path] = node
        edges: list[Edge] = []
        parent = current_by_path.get(instance.parent_path or "game")
        if parent and parent.id != node.id:
            edges.append(
                Edge.create(
                    project_id=event.project_id,
                    source_id=parent.id,
                    target_id=node.id,
                    type="CONTAINS",
                    metadata={"origin": "studio_event"},
                )
            )
        analysis = self.analyzers.analyze_script(
            event.project_id, node, list(current_by_path.values())
        )
        analysis_nodes = self._deduplicate_nodes(analysis.nodes)
        edges = self._deduplicate_edges([*edges, *analysis.edges])
        self.repository.replace_node_analysis(node, analysis_nodes, edges)
        return EventResult(event.project_id, "node_updated", analysis.warnings)

    def _was_just_removed(self, project_id: str, path: str) -> bool:
        now = time.monotonic()
        self._recently_removed = {
            key: removed_at
            for key, removed_at in self._recently_removed.items()
            if now - removed_at < 3
        }
        return any(
            removed_project == project_id
            and (path == removed_path or path.startswith(f"{removed_path}."))
            for removed_project, removed_path in self._recently_removed
        )

    @staticmethod
    def _is_architectural(instance: StudioInstance) -> bool:
        return bool(instance.name) and bool(instance.class_name) and (
            instance.is_service or instance.class_name in _TYPE_BY_CLASS_NAME
        )

    @staticmethod
    def _to_node(project_id: str, instance: StudioInstance) -> Node:
        source_hash = None
        if instance.source is not None:
            source_hash = hashlib.sha256(instance.source.encode("utf-8")).hexdigest()
        node_type = "Service" if instance.is_service else _TYPE_BY_CLASS_NAME[instance.class_name]
        return Node.create(
            project_id=project_id,
            type=node_type,
            name=instance.name,
            path=instance.path,
            metadata={
                "class_name": instance.class_name,
                "studio_id": instance.studio_id,
                "attributes": instance.attributes,
                "tags": instance.tags,
            },
            source=instance.source,
            source_hash=source_hash,
        )

    @staticmethod
    def _deduplicate_nodes(nodes: list[Node]) -> list[Node]:
        return list({node.id: node for node in nodes}.values())

    @staticmethod
    def _deduplicate_edges(edges: list[Edge]) -> list[Edge]:
        return list({edge.id: edge for edge in edges}.values())
