import asyncio
import json
from pathlib import Path

from mcp import Client

from roblox_graph.config import Settings
from roblox_graph.main import create_app
from roblox_graph.mcp.server import create_mcp_server
from roblox_graph.mcp.tools import GraphTools
from roblox_graph.models.studio import StudioSnapshot
from roblox_graph.storage.repositories import GraphRepository


def test_graph_tools_expose_read_only_project_inspection(tmp_path: Path) -> None:
    app = create_app(Settings(database_path=tmp_path / "graph.db"))
    fixture = Path(__file__).parent / "fixtures" / "analysis_game.json"
    app.state.studio_ingestion.ingest_snapshot(
        StudioSnapshot.model_validate(json.loads(fixture.read_text(encoding="utf-8")))
    )
    tools = GraphTools(GraphRepository(app.state.repository.database))

    search = tools.search_project("place:456", "InventoryService")
    controller = search["results"][0]
    assert controller["name"] == "InventoryService"

    dependencies = tools.get_dependencies(controller["id"], depth=2)
    assert any(node["type"] == "RemoteEvent" for node in dependencies["dependencies"])
    assert tools.get_script(controller["id"])["source"]
    assert tools.find_remote_usage("place:456")["targets"]
    assert tools.find_datastore_usage("place:456")["targets"]
    assert tools.find_tag_usage("place:456")["targets"]
    assert tools.find_attribute_usage("place:456")["targets"]
    assert tools.get_project_overview("place:456")["nodes"] > 0
    assert tools.get_god_nodes("place:456")["nodes"]


def test_mcp_server_registers_rograph_inspection_tools(tmp_path: Path) -> None:
    async def list_tool_names() -> set[str]:
        server = create_mcp_server(Settings(database_path=tmp_path / "graph.db"))
        async with Client(server) as client:
            result = await client.list_tools()
            return {tool.name for tool in result.tools}

    names = asyncio.run(list_tool_names())
    assert {
        "search_project",
        "get_script",
        "get_dependencies",
        "find_remote_usage",
        "get_god_nodes",
    } <= names
