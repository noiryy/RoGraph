"""Translate Roblox Studio snapshots into the canonical graph domain."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from roblox_graph.models.edge import Edge
from roblox_graph.models.node import Node
from roblox_graph.models.project import Project
from roblox_graph.models.studio import StudioInstance, StudioSnapshot
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


class StudioIngestionService:
    """Ingest full snapshots; incremental events are intentionally a later phase."""

    def __init__(self, repository: GraphRepository) -> None:
        self.repository = repository

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

        self.repository.replace_project_graph(project, nodes, edges)
        return IngestionResult(project=project, nodes=nodes, edges=edges)

    @staticmethod
    def _is_architectural(instance: StudioInstance) -> bool:
        return instance.is_service or instance.class_name in _TYPE_BY_CLASS_NAME

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
