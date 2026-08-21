"""Application factory and command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from roblox_graph.api.graph import router as graph_router
from roblox_graph.api.studio import router as studio_router
from roblox_graph.config import Settings
from roblox_graph.graph.engine import GraphEngine
from roblox_graph.storage.database import Database
from roblox_graph.storage.repositories import GraphRepository
from roblox_graph.studio_ingestion import StudioIngestionService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_environment()
    database = Database(settings.database_path)
    database.initialize()
    repository = GraphRepository(database)
    app = FastAPI(title="RoGraph", version="0.1.0")
    app.state.settings = settings
    app.state.repository = repository
    app.state.graph = GraphEngine(repository)
    app.state.studio_ingestion = StudioIngestionService(repository)
    app.state.studio_connected = False
    app.state.last_studio_update = None
    app.include_router(graph_router)
    app.include_router(studio_router)
    web_dir = Path(__file__).with_name("web")
    app.mount("/static", StaticFiles(directory=web_dir), name="static")

    @app.get("/", include_in_schema=False)
    def graph_view() -> FileResponse:
        return FileResponse(web_dir / "index.html")

    @app.get("/api/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/status", tags=["system"])
    def status() -> dict[str, object]:
        last_update = app.state.last_studio_update
        return {
            "studio_connected": app.state.studio_connected,
            "last_update": last_update.isoformat() if last_update else None,
            **repository.stats(),
        }

    return app


def main() -> None:
    parser = argparse.ArgumentParser(prog="roblox-graph")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("serve", help="Start the local API server")
    subparsers.add_parser("stats", help="Print persisted graph counts")
    subparsers.add_parser("doctor", help="Verify database initialization")
    arguments = parser.parse_args()
    settings = Settings.from_environment()

    if arguments.command == "serve":
        uvicorn.run(create_app(settings), host=settings.host, port=settings.port)
    else:
        database = Database(settings.database_path)
        database.initialize()
        stats = GraphRepository(database).stats()
        if arguments.command == "doctor":
            print(f"Database ready: {settings.database_path}")
        print(json.dumps(stats, indent=2))


app = create_app()

if __name__ == "__main__":
    main()
