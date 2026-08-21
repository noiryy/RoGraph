"""Local-only endpoint consumed by the Roblox Studio plugin."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Request, status

from roblox_graph.models.studio import StudioSnapshot

router = APIRouter(prefix="/api/studio", tags=["studio"])


@router.post("/snapshot", status_code=status.HTTP_202_ACCEPTED)
def post_snapshot(snapshot: StudioSnapshot, request: Request) -> dict[str, object]:
    result = request.app.state.studio_ingestion.ingest_snapshot(snapshot)
    request.app.state.studio_connected = True
    request.app.state.last_studio_update = datetime.now(UTC)
    return {
        "project_id": result.project.id,
        "nodes_indexed": len(result.nodes),
        "edges_indexed": len(result.edges),
        "warnings": result.warnings,
    }
