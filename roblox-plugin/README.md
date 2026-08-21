# RoGraph Studio plugin

This is a read-only local plugin. It scans meaningful DataModel objects and sends one full snapshot to `http://127.0.0.1:8765/api/studio/snapshot` when you click **RoGraph → Index Project**.

## Install for development

1. In Roblox Studio, create a `Script` named `RoGraph` and place three `ModuleScript` children beneath it: `Scanner`, `Serializer`, and `HttpClient`.
2. Copy the matching files from this folder into those Studio scripts.
3. Select the root `RoGraph` script and choose **Plugins → Save as Local Plugin**.
4. Start the backend with `uv run roblox-graph serve`, reopen Studio, and click **Index Project**.

The first HTTP request may ask permission for the plugin to access `127.0.0.1`. Approve only that loopback address. The plugin never writes to the open place or exposes the backend to the network.

## Current scan boundary

The snapshot includes root services, folders, models, scripts, remotes, bindables, attributes, tags, and readable script source. After a successful initial index, changes to these meaningful entities are sent after a 750ms debounce. Individual parts and other low-level instances are intentionally excluded to keep the graph architectural.
