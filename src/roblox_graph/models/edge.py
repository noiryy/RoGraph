"""Graph edge model and deterministic identifiers."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, Field


def stable_edge_id(
    project_id: str,
    source_id: str,
    target_id: str,
    edge_type: str,
    metadata: dict[str, Any],
) -> str:
    stable_metadata = json.dumps(metadata, sort_keys=True, separators=(",", ":"), default=str)
    identity = "|".join((project_id, source_id, target_id, edge_type, stable_metadata))
    return f"edge:{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:20]}"


class Edge(BaseModel):
    id: str
    project_id: str
    source_id: str
    target_id: str
    type: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        project_id: str,
        source_id: str,
        target_id: str,
        type: str,
        metadata: dict[str, Any] | None = None,
    ) -> Edge:
        value = metadata or {}
        return cls(
            id=stable_edge_id(project_id, source_id, target_id, type, value),
            project_id=project_id,
            source_id=source_id,
            target_id=target_id,
            type=type,
            metadata=value,
        )
