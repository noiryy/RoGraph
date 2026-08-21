import json
from pathlib import Path

from fastapi.testclient import TestClient

from roblox_graph.config import Settings
from roblox_graph.main import create_app


def test_snapshot_ingests_architectural_instances_and_replaces_stale_nodes(tmp_path: Path) -> None:
    app = create_app(Settings(database_path=tmp_path / "graph.db"))
    client = TestClient(app)
    fixture = Path(__file__).parent / "fixtures" / "simple_game.json"
    snapshot = json.loads(fixture.read_text(encoding="utf-8"))

    response = client.post("/api/studio/snapshot", json=snapshot)

    assert response.status_code == 202
    assert response.json() == {
        "project_id": "place:123",
        "nodes_indexed": 6,
        "edges_indexed": 5,
        "warnings": [],
    }
    status = client.get("/api/status").json()
    assert status["studio_connected"] is True
    assert status["nodes"] == 6
    assert status["edges"] == 5

    graph = client.get("/api/graph", params={"project_id": "place:123"}).json()
    inventory = next(node for node in graph["nodes"] if node["name"] == "Inventory")
    assert inventory["source_hash"]
    assert inventory["metadata"]["tags"] == ["Shared"]
    assert "UnimportantPart" not in {node["name"] for node in graph["nodes"]}

    snapshot["instances"] = snapshot["instances"][:-2]
    replacement = client.post("/api/studio/snapshot", json=snapshot)
    assert replacement.json()["nodes_indexed"] == 5
    assert replacement.json()["edges_indexed"] == 4


def test_snapshot_accepts_roblox_empty_attribute_tables_and_skips_empty_class_names(
    tmp_path: Path,
) -> None:
    app = create_app(Settings(database_path=tmp_path / "graph.db"))
    client = TestClient(app)
    fixture = Path(__file__).parent / "fixtures" / "simple_game.json"
    snapshot = json.loads(fixture.read_text(encoding="utf-8"))
    for instance in snapshot["instances"]:
        instance["attributes"] = []
    snapshot["instances"].append(
        {
            "name": "FilteredSelection",
            "className": "",
            "path": "FilteredSelection",
            "parentPath": "game",
            "isService": False,
            "attributes": [],
            "tags": [],
        }
    )

    response = client.post("/api/studio/snapshot", json=snapshot)

    assert response.status_code == 202
    graph = client.get("/api/graph", params={"project_id": "place:123"}).json()
    assert all(node["name"] != "FilteredSelection" for node in graph["nodes"])


def test_snapshot_accepts_and_skips_unnamed_roblox_instances(tmp_path: Path) -> None:
    app = create_app(Settings(database_path=tmp_path / "graph.db"))
    client = TestClient(app)
    fixture = Path(__file__).parent / "fixtures" / "simple_game.json"
    snapshot = json.loads(fixture.read_text(encoding="utf-8"))
    snapshot["instances"].append(
        {
            "id": "unnamed-model",
            "name": "",
            "className": "Model",
            "path": "ReplicatedStorage.",
            "parentPath": "ReplicatedStorage",
            "attributes": [],
            "tags": [],
        }
    )

    response = client.post("/api/studio/snapshot", json=snapshot)

    assert response.status_code == 202
    graph = client.get("/api/graph", params={"project_id": "place:123"}).json()
    assert all(node["name"] for node in graph["nodes"])


def test_studio_events_update_and_remove_a_node_with_websocket_notification(tmp_path: Path) -> None:
    app = create_app(Settings(database_path=tmp_path / "graph.db"))
    client = TestClient(app)
    fixture = Path(__file__).parent / "fixtures" / "simple_game.json"
    snapshot = json.loads(fixture.read_text(encoding="utf-8"))
    client.post("/api/studio/snapshot", json=snapshot)
    inventory = next(
        instance for instance in snapshot["instances"] if instance["name"] == "Inventory"
    )
    inventory["source"] = "return { MaxItems = 250 }"

    with client.websocket_connect("/ws/graph") as socket:
        updated = client.post(
            "/api/studio/events",
            json={"project_id": "place:123", "kind": "upsert", "instance": inventory},
        )
        assert updated.json() == {"event_type": "node_updated", "warnings": []}
        assert socket.receive_json() == {"type": "node_updated", "project_id": "place:123"}

        removed = client.post(
            "/api/studio/events",
            json={
                "project_id": "place:123",
                "kind": "remove",
                "path": "ReplicatedStorage.Purchase",
            },
        )
        assert removed.json() == {"event_type": "node_removed", "warnings": []}
        assert socket.receive_json() == {"type": "node_removed", "project_id": "place:123"}

    graph = client.get("/api/graph", params={"project_id": "place:123"}).json()
    changed = next(node for node in graph["nodes"] if node["name"] == "Inventory")
    assert changed["source"] == "return { MaxItems = 250 }"
    assert all(node["name"] != "Purchase" for node in graph["nodes"])


def test_remove_event_removes_a_node_subtree(tmp_path: Path) -> None:
    app = create_app(Settings(database_path=tmp_path / "graph.db"))
    client = TestClient(app)
    fixture = Path(__file__).parent / "fixtures" / "simple_game.json"
    client.post("/api/studio/snapshot", json=json.loads(fixture.read_text(encoding="utf-8")))

    response = client.post(
        "/api/studio/events",
        json={"project_id": "place:123", "kind": "remove", "path": "ReplicatedStorage"},
    )

    assert response.json()["event_type"] == "node_removed"
    graph = client.get("/api/graph", params={"project_id": "place:123"}).json()
    assert {"ReplicatedStorage", "Modules", "Inventory", "Purchase"}.isdisjoint(
        {node["name"] for node in graph["nodes"]}
    )


def test_delayed_child_upsert_does_not_recreate_a_recently_removed_subtree(tmp_path: Path) -> None:
    app = create_app(Settings(database_path=tmp_path / "graph.db"))
    client = TestClient(app)
    fixture = Path(__file__).parent / "fixtures" / "simple_game.json"
    snapshot = json.loads(fixture.read_text(encoding="utf-8"))
    client.post("/api/studio/snapshot", json=snapshot)
    child = next(instance for instance in snapshot["instances"] if instance["name"] == "Inventory")
    client.post(
        "/api/studio/events",
        json={"project_id": "place:123", "kind": "remove", "path": "ReplicatedStorage"},
    )

    delayed = client.post(
        "/api/studio/events",
        json={"project_id": "place:123", "kind": "upsert", "instance": child},
    )

    assert delayed.json() == {"event_type": "node_unchanged", "warnings": []}
    graph = client.get("/api/graph", params={"project_id": "place:123"}).json()
    assert all(node["name"] != "Inventory" for node in graph["nodes"])
