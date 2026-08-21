# Phase 1–2 architecture decisions

## The graph engine does not know about transports

`GraphEngine` depends only on the small repository interface implemented by `GraphRepository`. FastAPI, a future MCP server, and the Studio bridge should call this shared service rather than querying SQLite directly.

## SQLite is the durable source of truth

The application retains the most recently indexed graph while Studio is unavailable. SQLite uses explicit tables and indexes now, so the future incremental indexer can replace a script's outgoing analysis edges without rebuilding the project.

## IDs are deterministic

Nodes derive their ID from project ID, node type, and path (or name when no path is known). Edges derive theirs from their project, endpoints, type, and stable metadata. This avoids graph churn during future snapshot updates.

## MVP remains local and read-only

The default host is loopback. There are no execute or mutation endpoints for Roblox Studio; the only write operations currently available are internal storage methods used by trusted indexing code.

## Studio owns DataModel discovery

The plugin sends a validated, full snapshot of meaningful DataModel entities because the Python backend cannot inspect the open Studio place itself. The backend derives graph IDs from paths rather than trusting Studio debug IDs, which keeps snapshots reproducible across scans. Full replacement is intentionally limited to this phase; later incremental events will replace only an affected node's analysis edges.

## Static analysis is conservative and composable

Each analyzer receives a script plus a read-only project context and returns nodes, edges, and warnings. The MVP only creates relationship edges when a direct DataModel path can be resolved. Dynamic values are not represented as invented targets; they remain warnings until a future analysis or runtime signal can establish them.
