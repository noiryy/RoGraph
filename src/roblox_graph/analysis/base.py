"""Shared contracts for small, independently testable Luau analyzers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from roblox_graph.models.edge import Edge
from roblox_graph.models.node import Node


@dataclass(frozen=True, slots=True)
class ProjectContext:
    project_id: str
    nodes_by_path: dict[str, Node]

    def node_at(self, path: str) -> Node | None:
        return self.nodes_by_path.get(path)


@dataclass(slots=True)
class AnalysisResult:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def extend(self, other: AnalysisResult) -> None:
        self.nodes.extend(other.nodes)
        self.edges.extend(other.edges)
        self.warnings.extend(other.warnings)


class Analyzer(Protocol):
    def analyze(self, script: Node, project: ProjectContext) -> AnalysisResult: ...
