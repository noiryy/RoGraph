"""Detect ``game:GetService()`` dependencies."""

from __future__ import annotations

import re

from roblox_graph.analysis.base import AnalysisResult, ProjectContext
from roblox_graph.analysis.utils import metadata_for
from roblox_graph.models.edge import Edge
from roblox_graph.models.node import Node

_GET_SERVICE = re.compile(r"\bgame\s*:\s*GetService\s*\(\s*[\"']([^\"']+)[\"']\s*\)")


class ServiceAnalyzer:
    def analyze(self, script: Node, project: ProjectContext) -> AnalysisResult:
        result = AnalysisResult()
        if script.source is None:
            return result
        for match in _GET_SERVICE.finditer(script.source):
            service_name = match.group(1)
            target = project.node_at(service_name)
            if target is None:
                result.warnings.append(f"{script.path}: service {service_name!r} is not indexed")
                continue
            result.edges.append(
                Edge.create(
                    project_id=project.project_id,
                    source_id=script.id,
                    target_id=target.id,
                    type="USES_SERVICE",
                    metadata=metadata_for(script.source, match.start(), service_name),
                )
            )
        return result
