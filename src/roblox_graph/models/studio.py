"""Validated payloads received from the local Roblox Studio bridge."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StudioProject(BaseModel):
    id: str = Field(min_length=1, max_length=256)
    name: str = Field(min_length=1, max_length=256)
    place_id: str | None = Field(default=None, max_length=256)


class StudioInstance(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    class_name: str = Field(min_length=1, max_length=256, alias="className")
    path: str = Field(min_length=1, max_length=2048)
    parent_path: str | None = Field(default=None, max_length=2048, alias="parentPath")
    studio_id: str | None = Field(default=None, max_length=512, alias="id")
    source: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    is_service: bool = Field(default=False, alias="isService")


class StudioSnapshot(BaseModel):
    project: StudioProject
    instances: list[StudioInstance] = Field(default_factory=list, max_length=20_000)
