from fastapi.testclient import TestClient

from roblox_graph.config import Settings
from roblox_graph.main import create_app


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
