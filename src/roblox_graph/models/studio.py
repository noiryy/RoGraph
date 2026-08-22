"""Validated payloads received from the local Roblox Studio bridge."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class StudioProject(BaseModel):
    id: str = Field(min_length=1, max_length=256)
    name: str = Field(min_length=1, max_length=256)
    place_id: str | None = Field(default=None, max_length=256)


class StudioInstance(BaseModel):
    # Roblox permits unnamed instances.  They cannot be represented as unique
    # graph nodes, but accepting them here lets ingestion safely skip them
    # instead of rejecting the entire Studio snapshot.
    name: str = Field(max_length=256)
    class_name: str = Field(max_length=256, alias="className")
    instance_class_name: str | None = Field(
        default=None, max_length=256, alias="instanceClassName"
    )
    path: str = Field(min_length=1, max_length=2048)
    parent_path: str | None = Field(default=None, max_length=2048, alias="parentPath")
    studio_id: str | None = Field(default=None, max_length=512, alias="id")
    source: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    is_service: bool = Field(default=False, alias="isService")

    @field_validator("attributes", mode="before")
    @classmethod
    def normalize_empty_attribute_tables(cls, value: object) -> object:
        """Roblox encodes a table with no keys as JSON ``[]`` rather than ``{}``."""
        return {} if value == [] else value


class StudioSnapshot(BaseModel):
    project: StudioProject
    instances: list[StudioInstance] = Field(default_factory=list, max_length=20_000)


class StudioEvent(BaseModel):
    project_id: str = Field(min_length=1, max_length=256)
    kind: Literal["upsert", "remove"]
    instance: StudioInstance | None = None
    path: str | None = Field(default=None, max_length=2048)

    @model_validator(mode="after")
    def validate_payload(self) -> StudioEvent:
        if self.kind == "upsert" and self.instance is None:
            raise ValueError("upsert events require an instance")
        if self.kind == "remove" and not self.path:
            raise ValueError("remove events require a path")
        return self
