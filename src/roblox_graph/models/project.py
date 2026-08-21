"""Project model."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Project(BaseModel):
    id: str
    name: str
    place_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
