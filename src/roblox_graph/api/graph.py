"""Read-only graph inspection endpoints."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter(prefix="/api", tags=["graph"])


MAX_DEPTH = 4


def _get_existing_node(request: Request, node_id: str) -> object:
    node = request.app.state.graph.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.get("/projects")
def list_projects(request: Request) -> dict[str, object]:
    return {"projects": request.app.state.repository.list_projects()}


@router.get("/projects/{project_id}/overview")
def get_project_overview(request: Request, project_id: str) -> dict[str, object]:
    return request.app.state.intelligence.overview(project_id)


@router.get("/projects/{project_id}/god-nodes")
def get_god_nodes(
    request: Request,
    project_id: str,
    limit: int = Query(default=10, ge=1, le=100),
) -> dict[str, object]:
    return {"nodes": request.app.state.intelligence.god_nodes(project_id, limit=limit)}


@router.get("/graph")
def get_graph(
    request: Request,
    project_id: str,
    limit: int = Query(default=3_000, ge=1, le=10_000),
    order: Literal["name", "connected"] = "name",
    edge_limit: int | None = Query(default=None, ge=1, le=20_000),
    include_source: bool = False,
    lens: Literal["all", "client_ui"] = "all",
) -> dict[str, object]:
    repository = request.app.state.repository
    if lens == "client_ui":
        nodes = [
            node
            for node in repository.list_nodes(project_id)
            if node.metadata.get("execution_context") == "client"
            or node.metadata.get("ui_component") is True
            or node.type == "LocalScript"
            or (node.path or "").startswith(("StarterPlayer", "StarterGui", "StarterPack"))
        ][:limit]
    else:
        nodes = (
            repository.list_nodes_by_connectivity(project_id, limit=limit)
            if order == "connected"
            else repository.list_nodes(project_id, limit=limit)
        )
    node_ids = {node.id for node in nodes}
    edges = [
        edge
        for edge in repository.list_edges(project_id)
        if edge.source_id in node_ids and edge.target_id in node_ids
    ]
    if edge_limit is not None:
        edges.sort(key=lambda edge: (edge.type == "CONTAINS", edge.id))
        edges = edges[:edge_limit]
    return {
        "nodes": nodes
        if include_source
        else [node.model_copy(update={"source": None}) for node in nodes],
        "edges": edges,
    }


@router.get("/nodes/{node_id}")
def get_node(request: Request, node_id: str) -> object:
    return _get_existing_node(request, node_id)


@router.get("/nodes/{node_id}/neighbors")
def get_neighbors(request: Request, node_id: str, direction: str = "both") -> dict[str, object]:
    node = _get_existing_node(request, node_id)
    try:
        neighbors = request.app.state.graph.get_neighbors(node_id, direction=direction)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"node": node, "neighbors": neighbors}


@router.get("/nodes/{node_id}/dependencies")
def get_dependencies(
    request: Request,
    node_id: str,
    depth: int = Query(default=1, ge=1, le=MAX_DEPTH),
) -> dict[str, object]:
    node = _get_existing_node(request, node_id)
    return {
        "node": node,
        "dependencies": request.app.state.graph.get_dependencies(node_id, depth=depth),
    }


@router.get("/nodes/{node_id}/dependents")
def get_dependents(
    request: Request,
    node_id: str,
    depth: int = Query(default=1, ge=1, le=MAX_DEPTH),
) -> dict[str, object]:
    node = _get_existing_node(request, node_id)
    return {
        "node": node,
        "dependents": request.app.state.graph.get_dependents(node_id, depth=depth),
    }


@router.get("/nodes/{node_id}/subgraph")
def get_subgraph(
    request: Request,
    node_id: str,
    depth: int = Query(default=1, ge=1, le=MAX_DEPTH),
) -> dict[str, object]:
    _get_existing_node(request, node_id)
    nodes, edges = request.app.state.graph.get_subgraph(node_id, depth=depth)
    return {"nodes": nodes, "edges": edges}


@router.get("/search")
def search_project(
    request: Request,
    project_id: str,
    query: str = Query(min_length=1, max_length=256),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, object]:
    return {
        "query": query,
        "results": request.app.state.graph.search_project(project_id, query, limit=limit),
    }
