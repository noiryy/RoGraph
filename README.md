# RoGraph

RoGraph is a local-first, read-only knowledge graph for Roblox Studio projects. It stores Roblox-aware structural relationships in SQLite and exposes them through a Python API, web viewer, and MCP server.

## Current vertical slice

Phase 2 provides a complete initial Studio-to-graph snapshot path:

- deterministic `Node` and `Edge` models;
- SQLite-backed storage;
- graph traversal and centrality operations independent of HTTP or MCP;
- a local FastAPI service with health, status, graph, node, and neighbor endpoints;
- a read-only Roblox Studio plugin and `POST /api/studio/snapshot` bridge;
- debounced Studio change events and live WebSocket graph refreshes;
- static analysis for direct `require()`, services, remotes, DataStores, tags, and attributes;
- a stdio MCP server with project search, script and dependency inspection, path tracing, and
  targeted remote/DataStore/tag/attribute queries;
- degree and weighted coupling metrics, deterministic relationship communities, and architecture
  summaries for the graph API, viewer, and MCP tools;
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

To connect an MCP-capable desktop agent, configure it to launch this local command from the
repository root:

```powershell
uv run roblox-graph mcp
```

The MCP server is read-only: it exposes inspection tools only and never changes Studio or source.

To index a place, install the [Studio plugin](roblox-plugin/README.md), then click **RoGraph → Index Project**. After the initial index, meaningful changes are debounced and sent to the bridge; connected graph viewers refresh automatically. The bridge analyzes direct, statically resolvable patterns and records line numbers and confidence on generated edges. Dynamic expressions are returned as snapshot warnings rather than guessed. See [docs/architecture.md](docs/architecture.md) for the boundaries.
