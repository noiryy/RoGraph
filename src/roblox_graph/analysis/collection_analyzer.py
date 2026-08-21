"""Detect CollectionService tag use."""

from __future__ import annotations

import re

from roblox_graph.analysis.base import AnalysisResult, ProjectContext
from roblox_graph.analysis.utils import metadata_for
from roblox_graph.models.edge import Edge
from roblox_graph.models.node import Node

_TAG_USE = re.compile(
    r"(?:CollectionService|[\w.]+CollectionService)\s*:\s*"
    r"(?P<method>GetTagged|HasTag|AddTag|RemoveTag)\s*\([^,]*,?\s*[\"'](?P<tag>[^\"']+)[\"']"
)


class CollectionAnalyzer:
    def analyze(self, script: Node, project: ProjectContext) -> AnalysisResult:
        result = AnalysisResult()
        if script.source is None:
            return result
        for match in _TAG_USE.finditer(script.source):
            tag = match.group("tag")
            node = Node.create(
                project_id=project.project_id,
                type="CollectionServiceTag",
                name=tag,
                path=f"Tag:{tag}",
                metadata={"origin": "static"},
            )
            result.nodes.append(node)
            result.edges.append(
                Edge.create(
                    project_id=project.project_id,
                    source_id=script.id,
                    target_id=node.id,
                    type="USES_TAG",
                    metadata=metadata_for(script.source, match.start(), tag)
                    | {"method": match.group("method")},
                )
            )
        return result
