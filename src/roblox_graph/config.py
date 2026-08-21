"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 8765
    database_path: Path = Path(".data/graph.db")
    source_debounce_ms: int = 750
    max_graph_depth: int = 4
    max_results: int = 100

    @classmethod
    def from_environment(cls) -> Settings:
        return cls(
            host=os.getenv("ROGRAPH_HOST", "127.0.0.1"),
            port=int(os.getenv("ROGRAPH_PORT", "8765")),
            database_path=Path(os.getenv("ROGRAPH_DATABASE_PATH", ".data/graph.db")),
            source_debounce_ms=int(os.getenv("ROGRAPH_SOURCE_DEBOUNCE_MS", "750")),
            max_graph_depth=int(os.getenv("ROGRAPH_MAX_GRAPH_DEPTH", "4")),
            max_results=int(os.getenv("ROGRAPH_MAX_RESULTS", "100")),
        )
