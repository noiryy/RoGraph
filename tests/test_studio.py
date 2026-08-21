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
