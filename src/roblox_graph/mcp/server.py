"""A stdio MCP server that exposes the local RoGraph database."""

from __future__ import annotations

from mcp.server import MCPServer

from roblox_graph.config import Settings
from roblox_graph.mcp.tools import GraphTools
from roblox_graph.storage.database import Database
from roblox_graph.storage.repositories import GraphRepository


def create_mcp_server(settings: Settings | None = None) -> MCPServer:
    """Create an MCP server backed by the configured local SQLite database."""
    settings = settings or Settings.from_environment()
    database = Database(settings.database_path)
    database.initialize()
    tools = GraphTools(GraphRepository(database))
    server = MCPServer(
        "RoGraph",
        description="Read-only knowledge graph inspection for a local Roblox Studio project.",
        instructions=(
            "Use these tools to inspect the indexed Roblox project. "
            "They never modify Studio or code."
        ),
        version="0.1.0",
    )

    @server.tool()
    def search_project(project_id: str, query: str, limit: int = 20) -> dict[str, object]:
        """Search names, paths, types, and source in one indexed project."""
        return tools.search_project(project_id, query, limit)

    @server.tool()
    def get_node(node_id: str) -> dict[str, object]:
        """Get the stored metadata for one graph node."""
        return tools.get_node(node_id)

    @server.tool()
    def get_script(node_id: str) -> dict[str, object]:
        """Get a script node and its indexed Luau source."""
        return tools.get_script(node_id)

    @server.tool()
    def get_dependencies(node_id: str, depth: int = 1) -> dict[str, object]:
        """Traverse outgoing graph relationships from a node."""
        return tools.get_dependencies(node_id, depth)

    @server.tool()
    def get_dependents(node_id: str, depth: int = 1) -> dict[str, object]:
        """Traverse incoming graph relationships to a node."""
        return tools.get_dependents(node_id, depth)

    @server.tool()
    def get_related(node_id: str, limit: int = 25) -> dict[str, object]:
        """Get direct neighbors ranked by relationship strength."""
        return tools.get_related(node_id, limit)

    @server.tool()
    def get_subgraph(node_id: str, depth: int = 1) -> dict[str, object]:
        """Return the nodes and edges around a graph node."""
        return tools.get_subgraph(node_id, depth)

    @server.tool()
    def trace_path(source_id: str, target_id: str) -> dict[str, object]:
        """Find a directed shortest relationship path between two nodes."""
        return tools.trace_path(source_id, target_id)

    @server.tool()
    def find_remote_usage(project_id: str, name: str | None = None) -> dict[str, object]:
        """Find RemoteEvent and RemoteFunction nodes and their incoming usages."""
        return tools.find_remote_usage(project_id, name)

    @server.tool()
    def find_datastore_usage(project_id: str, name: str | None = None) -> dict[str, object]:
        """Find DataStore nodes and their read/write usages."""
        return tools.find_datastore_usage(project_id, name)

    @server.tool()
    def find_tag_usage(project_id: str, name: str | None = None) -> dict[str, object]:
        """Find CollectionService tag nodes and their usages."""
        return tools.find_tag_usage(project_id, name)

    @server.tool()
    def find_attribute_usage(project_id: str, name: str | None = None) -> dict[str, object]:
        """Find attribute nodes and their read/write usages."""
        return tools.find_attribute_usage(project_id, name)

    @server.tool()
    def get_project_overview(project_id: str) -> dict[str, object]:
        """Summarize an indexed project's graph size and node types."""
        return tools.get_project_overview(project_id)

    @server.tool()
    def get_god_nodes(project_id: str, limit: int = 10) -> dict[str, object]:
        """Return the highest-degree nodes in an indexed project."""
        return tools.get_god_nodes(project_id, limit)

    return server


def main() -> None:
    create_mcp_server().run(transport="stdio")


if __name__ == "__main__":
    main()
