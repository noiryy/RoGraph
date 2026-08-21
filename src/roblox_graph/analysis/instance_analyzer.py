"""Detect direct ``GetAttribute`` and ``SetAttribute`` calls."""

from __future__ import annotations

import re

from roblox_graph.analysis.base import AnalysisResult, ProjectContext
from roblox_graph.analysis.utils import metadata_for
from roblox_graph.models.edge import Edge
from roblox_graph.models.node import Node

_ATTRIBUTE_USE = re.compile(
    r"\b[\w.]+\s*:\s*(?P<method>GetAttribute|SetAttribute)\s*"
    r"\(\s*[\"'](?P<name>[^\"']+)[\"']"
)


class InstanceAnalyzer:
    def analyze(self, script: Node, project: ProjectContext) -> AnalysisResult:
        result = AnalysisResult()
        if script.source is None:
            return result
        for match in _ATTRIBUTE_USE.finditer(script.source):
            name = match.group("name")
            node = Node.create(
                project_id=project.project_id,
                type="Attribute",
                name=name,
                path=f"Attribute:{name}",
                metadata={"origin": "static"},
            )
            result.nodes.append(node)
            result.edges.append(
                Edge.create(
                    project_id=project.project_id,
                    source_id=script.id,
                    target_id=node.id,
                    type="READS_ATTRIBUTE"
                    if match.group("method") == "GetAttribute"
                    else "WRITES_ATTRIBUTE",
                    metadata=metadata_for(script.source, match.start(), name)
                    | {"method": match.group("method")},
                )
            )
        return result
