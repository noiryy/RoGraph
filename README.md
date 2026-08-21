# RoGraph

RoGraph is a local-first, read-only knowledge graph for Roblox Studio projects. It stores Roblox-aware structural relationships in SQLite and exposes them through a Python API, with a web viewer and MCP interface planned in later phases.

## Current vertical slice

Phase 2 provides a complete initial Studio-to-graph snapshot path:

- deterministic `Node` and `Edge` models;
- SQLite-backed storage;
- graph traversal and centrality operations independent of HTTP or MCP;
- a local FastAPI service with health, status, graph, node, and neighbor endpoints;
- a read-only Roblox Studio plugin and `POST /api/studio/snapshot` bridge;
- static analysis for direct `require()`, services, remotes, DataStores, tags, and attributes;
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

To index a place, install the [Studio plugin](roblox-plugin/README.md), then click **RoGraph → Index Project**. The bridge analyzes direct, statically resolvable patterns and records line numbers and confidence on generated edges. Dynamic expressions are returned as snapshot warnings rather than guessed. Incremental updates, the web graph, live updates, and MCP transport remain later phases. See [docs/architecture.md](docs/architecture.md) for the boundaries.
