"""Detect direct ``require()`` dependencies."""

from __future__ import annotations

import re

from roblox_graph.analysis.base import AnalysisResult, ProjectContext
from roblox_graph.analysis.utils import metadata_for, resolve_instance_expression
from roblox_graph.models.edge import Edge
from roblox_graph.models.node import Node

_REQUIRE = re.compile(r"\brequire\s*\(\s*([^()]+?)\s*\)")


class RequireAnalyzer:
    def analyze(self, script: Node, project: ProjectContext) -> AnalysisResult:
        result = AnalysisResult()
        if script.source is None:
            return result
        for match in _REQUIRE.finditer(script.source):
            expression = match.group(1)
            target = resolve_instance_expression(expression, script, project)
            if target is None:
                result.warnings.append(f"{script.path}: unresolved require({expression})")
                continue
            result.edges.append(
                Edge.create(
                    project_id=project.project_id,
                    source_id=script.id,
                    target_id=target.id,
                    type="REQUIRES",
                    metadata=metadata_for(script.source, match.start(), expression),
                )
            )
        return result
