"""Small deterministic community detection for architectural relationship clusters."""

from __future__ import annotations

from collections import deque

from roblox_graph.models.edge import Edge
from roblox_graph.models.node import Node


def find_communities(nodes: list[Node], edges: list[Edge]) -> dict[str, str]:
    """Return weakly connected components, excluding containment-only hierarchy links."""
    adjacency: dict[str, set[str]] = {node.id: set() for node in nodes}
    for edge in edges:
        if edge.type == "CONTAINS":
            continue
        if edge.source_id in adjacency and edge.target_id in adjacency:
            adjacency[edge.source_id].add(edge.target_id)
            adjacency[edge.target_id].add(edge.source_id)
    node_order = {node.id: (node.path or node.name, node.id) for node in nodes}
    components: list[list[str]] = []
    remaining = set(adjacency)
    while remaining:
        root = min(remaining, key=node_order.__getitem__)
        component: list[str] = []
        queue = deque([root])
        remaining.remove(root)
        while queue:
            current = queue.popleft()
            component.append(current)
            for neighbor in sorted(adjacency[current], key=node_order.__getitem__):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        components.append(component)
    components.sort(
        key=lambda members: (-len(members), min(node_order[node_id] for node_id in members))
    )
    return {
        node_id: f"community-{index:03d}"
        for index, members in enumerate(components, start=1)
        for node_id in members
    }
