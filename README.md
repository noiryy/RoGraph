# RoGraph

RoGraph is a local-first, read-only knowledge graph for Roblox Studio projects. It stores Roblox-aware structural relationships in SQLite and exposes them through a Python API, with a web viewer and MCP interface planned in later phases.

## Current vertical slice

Phase 1 provides the persistent graph core:

- deterministic `Node` and `Edge` models;
- SQLite-backed storage;
- graph traversal and centrality operations independent of HTTP or MCP;
- a local FastAPI service with health, status, graph, node, and neighbor endpoints;
- a CLI for serving and inspecting the graph.

## Quick start

```powershell
uv sync --extra dev
uv run roblox-graph serve
```

Open `http://127.0.0.1:8765/docs` to inspect the API. By default, data is stored in `.data/graph.db` and the server only binds to `127.0.0.1`.

```powershell
uv run roblox-graph stats
uv run roblox-graph doctor
uv run pytest
```

The Studio bridge, Luau analyzers, web graph, live updates, and MCP transport are deliberately not included yet. See [docs/architecture.md](docs/architecture.md) for the Phase 1 boundary.
