from fastapi.testclient import TestClient

from roblox_graph.config import Settings
from roblox_graph.main import create_app
from roblox_graph.models.edge import Edge
from roblox_graph.models.node import Node
from roblox_graph.models.project import Project


def test_health_and_status(tmp_path) -> None:
    app = create_app(Settings(database_path=tmp_path / "graph.db"))
    client = TestClient(app)

    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/status").json() == {
        "studio_connected": False,
        "last_update": None,
        "projects": 0,
        "nodes": 0,
        "edges": 0,
    }


def test_graph_api_search_and_traversal(tmp_path) -> None:
    app = create_app(Settings(database_path=tmp_path / "graph.db"))
    repository = app.state.repository
    repository.upsert_project(Project(id="place:test", name="Test"))
    controller = Node.create(
        project_id="place:test",
        type="LocalScript",
        name="ShopController",
        path="StarterPlayer.ShopController",
    )
    service = Node.create(
        project_id="place:test",
        type="ModuleScript",
        name="ShopService",
        path="ServerScriptService.ShopService",
        source="function purchase() end",
    )
    repository.upsert_node(controller)
    repository.upsert_node(service)
    repository.upsert_edge(
        Edge.create(
            project_id="place:test",
            source_id=controller.id,
            target_id=service.id,
            type="REQUIRES",
        )
    )
    client = TestClient(app)

    search = client.get("/api/search", params={"project_id": "place:test", "query": "shop"})
    assert [node["name"] for node in search.json()["results"]] == ["ShopController", "ShopService"]
    dependencies = client.get(f"/api/nodes/{controller.id}/dependencies").json()
    assert [node["id"] for node in dependencies["dependencies"]] == [service.id]
    subgraph = client.get(f"/api/nodes/{controller.id}/subgraph").json()
    assert len(subgraph["nodes"]) == 2
    assert len(subgraph["edges"]) == 1
    overview = client.get("/api/projects/place:test/overview").json()
    assert overview["community_count"] == 1
    assert overview["coupling_indicators"][0]["name"] in {"ShopController", "ShopService"}
    assert client.get("/api/projects/place:test/god-nodes").json()["nodes"]


def test_graph_view_and_projects_endpoint(tmp_path) -> None:
    app = create_app(Settings(database_path=tmp_path / "graph.db"))
    app.state.repository.upsert_project(Project(id="place:test", name="Test"))
    client = TestClient(app)

    assert client.get("/").status_code == 200
    assert "RoGraph" in client.get("/").text
    assert client.get("/api/projects").json()["projects"][0]["name"] == "Test"


def test_connected_graph_view_prioritizes_project_anchors_and_relationships(tmp_path) -> None:
    app = create_app(Settings(database_path=tmp_path / "graph.db"))
    repository = app.state.repository
    project = Project(id="place:large", name="Large")
    repository.upsert_project(project)
    place = Node.create(project_id=project.id, type="Place", name="Large", path="game")
    hub = Node.create(project_id=project.id, type="ModuleScript", name="Hub", path="Hub")
    leaf = Node.create(project_id=project.id, type="ModuleScript", name="Leaf", path="Leaf")
    for node in (place, hub, leaf):
        repository.upsert_node(node)
    repository.upsert_edge(
        Edge.create(
            project_id=project.id,
            source_id=hub.id,
            target_id=leaf.id,
            type="REQUIRES",
        )
    )

    response = TestClient(app).get(
        "/api/graph", params={"project_id": project.id, "limit": 2, "order": "connected"}
    )

    assert response.status_code == 200
    assert [node["name"] for node in response.json()["nodes"]] == ["Large", "Hub"]


def test_graph_view_omits_source_by_default_and_caps_preview_edges(tmp_path) -> None:
    app = create_app(Settings(database_path=tmp_path / "graph.db"))
    repository = app.state.repository
    project = Project(id="place:preview", name="Preview")
    repository.upsert_project(project)
    first = Node.create(
        project_id=project.id,
        type="ModuleScript",
        name="First",
        path="First",
        source="return 'large source payload'",
    )
    second = Node.create(project_id=project.id, type="ModuleScript", name="Second", path="Second")
    third = Node.create(project_id=project.id, type="ModuleScript", name="Third", path="Third")
    for node in (first, second, third):
        repository.upsert_node(node)
    repository.upsert_edge(
        Edge.create(project_id=project.id, source_id=first.id, target_id=second.id, type="REQUIRES")
    )
    repository.upsert_edge(
        Edge.create(project_id=project.id, source_id=second.id, target_id=third.id, type="CONTAINS")
    )

    preview = TestClient(app).get(
        "/api/graph",
        params={"project_id": project.id, "edge_limit": 1},
    ).json()
    full = TestClient(app).get(
        "/api/graph",
        params={"project_id": project.id, "include_source": True},
    ).json()

    assert all(node["source"] is None for node in preview["nodes"])
    assert len(preview["edges"]) == 1
    assert preview["edges"][0]["type"] == "REQUIRES"
    assert next(node for node in full["nodes"] if node["id"] == first.id)["source"]


def test_client_ui_lens_returns_only_client_and_ui_nodes(tmp_path) -> None:
    app = create_app(Settings(database_path=tmp_path / "graph.db"))
    repository = app.state.repository
    project = Project(id="place:lens", name="Lens")
    repository.upsert_project(project)
    client_script = Node.create(
        project_id=project.id,
        type="LocalScript",
        name="MenuController",
        path="StarterGui.MenuController",
        metadata={"execution_context": "client", "ui_component": False},
    )
    ui_component = Node.create(
        project_id=project.id,
        type="UIComponent",
        name="Play",
        path="StarterGui.Play",
        metadata={"execution_context": "client", "ui_component": True},
    )
    server_script = Node.create(
        project_id=project.id,
        type="Script",
        name="RoundService",
        path="ServerScriptService.RoundService",
        metadata={"execution_context": "server", "ui_component": False},
    )
    for node in (client_script, ui_component, server_script):
        repository.upsert_node(node)

    response = TestClient(app).get(
        "/api/graph", params={"project_id": project.id, "lens": "client_ui"}
    )

    assert {node["name"] for node in response.json()["nodes"]} == {"MenuController", "Play"}
