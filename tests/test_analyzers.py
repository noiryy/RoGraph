import json
from pathlib import Path

from fastapi.testclient import TestClient

from roblox_graph.config import Settings
from roblox_graph.main import create_app


def test_snapshot_generates_roblox_aware_static_edges(tmp_path: Path) -> None:
    app = create_app(Settings(database_path=tmp_path / "graph.db"))
    client = TestClient(app)
    fixture = Path(__file__).parent / "fixtures" / "analysis_game.json"

    response = client.post("/api/studio/snapshot", json=json.loads(fixture.read_text()))

    assert response.status_code == 202
    graph = client.get("/api/graph", params={"project_id": "place:456"}).json()
    edge_types = {edge["type"] for edge in graph["edges"]}
    node_types = {node["type"] for node in graph["nodes"]}
    assert {
        "REQUIRES",
        "USES_SERVICE",
        "FIRES",
        "LISTENS_TO",
        "READS",
        "WRITES",
        "USES_TAG",
        "READS_ATTRIBUTE",
        "WRITES_ATTRIBUTE",
    } <= edge_types
    assert {"DataStore", "CollectionServiceTag", "Attribute"} <= node_types

    requires = next(edge for edge in graph["edges"] if edge["type"] == "REQUIRES")
    assert requires["metadata"]["line"] == 4
    assert requires["metadata"]["confidence"] == 1.0
