"""Read-only graph inspection endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api", tags=["graph"])


@router.get("/graph")
def get_graph(request: Request, project_id: str) -> dict[str, object]:
    repository = request.app.state.repository
    return {
        "nodes": repository.list_nodes(project_id),
        "edges": repository.list_edges(project_id),
    }


@router.get("/nodes/{node_id}")
def get_node(request: Request, node_id: str) -> object:
    node = request.app.state.graph.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.get("/nodes/{node_id}/neighbors")
def get_neighbors(request: Request, node_id: str, direction: str = "both") -> dict[str, object]:
    node = request.app.state.graph.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    try:
        neighbors = request.app.state.graph.get_neighbors(node_id, direction=direction)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"node": node, "neighbors": neighbors}
