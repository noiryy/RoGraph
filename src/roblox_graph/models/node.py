"""Graph node model and deterministic identifiers."""

from __future__ import annotations

import hashlib
from typing import Any

from pydantic import BaseModel, Field


def stable_node_id(project_id: str, node_type: str, path: str | None, name: str) -> str:
    """Return a reproducible identifier for an architectural entity."""
    identity = "|".join((project_id, node_type, path or name))
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
    return f"{node_type.lower()}:{digest}"


class Node(BaseModel):
    id: str
    project_id: str
    type: str
    name: str
    path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: str | None = None
    source_hash: str | None = None

    @classmethod
    def create(
        cls,
        *,
        project_id: str,
        type: str,
        name: str,
        path: str | None = None,
        metadata: dict[str, Any] | None = None,
        source: str | None = None,
        source_hash: str | None = None,
    ) -> Node:
        return cls(
            id=stable_node_id(project_id, type, path, name),
            project_id=project_id,
            type=type,
            name=name,
            path=path,
            metadata=metadata or {},
            source=source,
            source_hash=source_hash,
        )
