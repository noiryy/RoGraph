"""Detect named DataStore creation and read/write operations."""

from __future__ import annotations

import re

from roblox_graph.analysis.base import AnalysisResult, ProjectContext
from roblox_graph.analysis.utils import metadata_for
from roblox_graph.models.edge import Edge
from roblox_graph.models.node import Node

_STORE_DECLARATION = re.compile(
    r"\blocal\s+(?P<variable>[A-Za-z_]\w*)\s*=\s*[\w.]+\s*:\s*"
    r"(?P<method>GetDataStore|GetOrderedDataStore)\s*\(\s*[\"'](?P<name>[^\"']+)[\"']"
)
_STORE_OPERATION = re.compile(
    r"\b(?P<variable>[A-Za-z_]\w*)\s*:\s*"
    r"(?P<method>GetAsync|SetAsync|UpdateAsync|RemoveAsync|IncrementAsync)\s*\("
)
_READS = {"GetAsync"}


class DataStoreAnalyzer:
    def analyze(self, script: Node, project: ProjectContext) -> AnalysisResult:
        result = AnalysisResult()
        if script.source is None:
            return result
        stores: dict[str, Node] = {}
        for match in _STORE_DECLARATION.finditer(script.source):
            name = match.group("name")
            store_type = (
                "OrderedDataStore"
                if match.group("method") == "GetOrderedDataStore"
                else "DataStore"
            )
            node = Node.create(
                project_id=project.project_id,
                type=store_type,
                name=name,
                path=f"{store_type}:{name}",
                metadata={"origin": "static", "factory": match.group("method")},
            )
            stores[match.group("variable")] = node
            result.nodes.append(node)
        for match in _STORE_OPERATION.finditer(script.source):
            store = stores.get(match.group("variable"))
            if store is None:
                continue
            operation = match.group("method")
            result.edges.append(
                Edge.create(
                    project_id=project.project_id,
                    source_id=script.id,
                    target_id=store.id,
                    type="READS" if operation in _READS else "WRITES",
                    metadata=metadata_for(script.source, match.start(), match.group("variable"))
                    | {"operation": operation},
                )
            )
        return result
