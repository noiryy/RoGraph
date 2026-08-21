"""Detect direct static RemoteEvent and RemoteFunction use."""

from __future__ import annotations

import re

from roblox_graph.analysis.base import AnalysisResult, ProjectContext
from roblox_graph.analysis.utils import metadata_for, resolve_instance_expression
from roblox_graph.models.edge import Edge
from roblox_graph.models.node import Node

_REMOTE_USE = re.compile(
    r"(?P<expression>(?:game\.|workspace\.|[A-Z][A-Za-z0-9_]*\.)[A-Za-z0-9_.]+)"
    r"\s*:\s*(?P<member>FireServer|FireClient|FireAllClients|InvokeServer|InvokeClient)\s*\("
)
_REMOTE_LISTEN = re.compile(
    r"(?P<expression>(?:game\.|workspace\.|[A-Z][A-Za-z0-9_]*\.)[A-Za-z0-9_.]+)"
    r"\s*\.\s*(?P<member>OnServerEvent|OnClientEvent|OnServerInvoke|OnClientInvoke)"
)


class RemoteAnalyzer:
    def analyze(self, script: Node, project: ProjectContext) -> AnalysisResult:
        result = AnalysisResult()
        if script.source is None:
            return result
        for match, edge_type in self._matches(script.source):
            expression = match.group("expression")
            target = resolve_instance_expression(expression, script, project)
            if target is None:
                result.warnings.append(f"{script.path}: unresolved remote {expression}")
                continue
            result.edges.append(
                Edge.create(
                    project_id=project.project_id,
                    source_id=script.id,
                    target_id=target.id,
                    type=edge_type,
                    metadata=metadata_for(
                        script.source,
                        match.start(),
                        expression,
                        confidence=1.0,
                    )
                    | {"member": match.group("member")},
                )
            )
        return result

    @staticmethod
    def _matches(source: str) -> list[tuple[re.Match[str], str]]:
        calls = [
            (match, "FIRES" if match.group("member").startswith("Fire") else "INVOKES")
            for match in _REMOTE_USE.finditer(source)
        ]
        listeners = [(match, "LISTENS_TO") for match in _REMOTE_LISTEN.finditer(source)]
        return [*calls, *listeners]
