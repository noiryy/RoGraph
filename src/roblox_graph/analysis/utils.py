"""Conservative source helpers shared by static analyzers."""

from __future__ import annotations

import re

from roblox_graph.analysis.base import ProjectContext
from roblox_graph.models.node import Node


def line_number(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def resolve_instance_expression(
    expression: str, script: Node, project: ProjectContext
) -> Node | None:
    """Resolve only direct, static DataModel paths; dynamic values return ``None``."""
    expression = re.sub(r"\s+", "", expression)
    if expression.startswith("game."):
        return project.node_at(expression.removeprefix("game."))
    if expression.startswith("workspace."):
        return project.node_at(f"Workspace.{expression.removeprefix('workspace.')}")
    if expression == "workspace":
        return project.node_at("Workspace")
    if expression == "script":
        return script
    if expression.startswith("script.") and script.path:
        parts = script.path.split(".")
        for part in expression.split(".")[1:]:
            if part == "Parent":
                if len(parts) <= 1:
                    return None
                parts.pop()
            else:
                parts.append(part)
        return project.node_at(".".join(parts))
    return project.node_at(expression)


def metadata_for(
    source: str, offset: int, expression: str, *, confidence: float = 1.0
) -> dict[str, object]:
    return {
        "line": line_number(source, offset),
        "expression": expression,
        "confidence": confidence,
        "origin": "static",
    }
