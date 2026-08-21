"""Compose small analyzers into the snapshot indexing pipeline."""

from __future__ import annotations

from collections.abc import Iterable

from roblox_graph.analysis.base import AnalysisResult, Analyzer, ProjectContext
from roblox_graph.analysis.collection_analyzer import CollectionAnalyzer
from roblox_graph.analysis.datastore_analyzer import DataStoreAnalyzer
from roblox_graph.analysis.instance_analyzer import InstanceAnalyzer
from roblox_graph.analysis.remote_analyzer import RemoteAnalyzer
from roblox_graph.analysis.require_analyzer import RequireAnalyzer
from roblox_graph.analysis.service_analyzer import ServiceAnalyzer
from roblox_graph.models.node import Node


class AnalyzerRunner:
    def __init__(self, analyzers: Iterable[Analyzer] | None = None) -> None:
        self.analyzers: list[Analyzer] = (
            list(analyzers)
            if analyzers is not None
            else [
                RequireAnalyzer(),
                ServiceAnalyzer(),
                RemoteAnalyzer(),
                DataStoreAnalyzer(),
                CollectionAnalyzer(),
                InstanceAnalyzer(),
            ]
        )

    def analyze_scripts(self, project_id: str, nodes: list[Node]) -> AnalysisResult:
        context = ProjectContext(
            project_id=project_id,
            nodes_by_path={node.path: node for node in nodes if node.path},
        )
        result = AnalysisResult()
        for script in nodes:
            if script.type not in {"Script", "LocalScript", "ModuleScript"}:
                continue
            for analyzer in self.analyzers:
                result.extend(analyzer.analyze(script, context))
        return result

    def analyze_script(self, project_id: str, script: Node, nodes: list[Node]) -> AnalysisResult:
        context = ProjectContext(
            project_id=project_id,
            nodes_by_path={node.path: node for node in nodes if node.path},
        )
        result = AnalysisResult()
        if script.type not in {"Script", "LocalScript", "ModuleScript"}:
            return result
        for analyzer in self.analyzers:
            result.extend(analyzer.analyze(script, context))
        return result
