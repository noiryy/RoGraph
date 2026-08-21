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
