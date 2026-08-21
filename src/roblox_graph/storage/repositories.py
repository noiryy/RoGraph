"""Repository operations used by graph services and future indexers."""

from __future__ import annotations

import json
import sqlite3

from roblox_graph.models.edge import Edge
from roblox_graph.models.node import Node
from roblox_graph.models.project import Project
from roblox_graph.storage.database import Database


class GraphRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def upsert_project(self, project: Project) -> Project:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO projects (id, name, place_id) VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET name = excluded.name, place_id = excluded.place_id,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (project.id, project.name, project.place_id),
            )
        return project

    def upsert_node(self, node: Node) -> Node:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO nodes (
                    id, project_id, type, name, path, metadata_json, source, source_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET type = excluded.type, name = excluded.name,
                    path = excluded.path, metadata_json = excluded.metadata_json,
                    source = excluded.source,
                    source_hash = excluded.source_hash, updated_at = CURRENT_TIMESTAMP
                """,
                self._node_values(node),
            )
        return node

    def upsert_edge(self, edge: Edge) -> Edge:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO edges (id, project_id, source_id, target_id, type, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET metadata_json = excluded.metadata_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                self._edge_values(edge),
            )
        return edge

    def replace_project_graph(self, project: Project, nodes: list[Node], edges: list[Edge]) -> None:
        """Atomically replace one project's graph after a full Studio snapshot."""
        if any(node.project_id != project.id for node in nodes):
            raise ValueError("Every node must belong to the snapshot project")
        if any(edge.project_id != project.id for edge in edges):
            raise ValueError("Every edge must belong to the snapshot project")

        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO projects (id, name, place_id) VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET name = excluded.name, place_id = excluded.place_id,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (project.id, project.name, project.place_id),
            )
            connection.execute("DELETE FROM nodes WHERE project_id = ?", (project.id,))
            connection.executemany(
                """
                INSERT INTO nodes (
                    id, project_id, type, name, path, metadata_json, source, source_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [self._node_values(node) for node in nodes],
            )
            connection.executemany(
                """
                INSERT INTO edges (id, project_id, source_id, target_id, type, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [self._edge_values(edge) for edge in edges],
            )

    def get_node(self, node_id: str) -> Node | None:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM nodes WHERE id = ?", (node_id,)).fetchone()
        return self._node_from_row(row) if row else None

    def get_node_by_path(self, project_id: str, path: str) -> Node | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM nodes WHERE project_id = ? AND path = ?", (project_id, path)
            ).fetchone()
        return self._node_from_row(row) if row else None

    def list_nodes(self, project_id: str, *, limit: int | None = None) -> list[Node]:
        query = "SELECT * FROM nodes WHERE project_id = ? ORDER BY name, id"
        params: tuple[object, ...] = (project_id,)
        if limit is not None:
            query += " LIMIT ?"
            params += (limit,)
        with self.database.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._node_from_row(row) for row in rows]

    def list_edges(self, project_id: str) -> list[Edge]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM edges WHERE project_id = ? ORDER BY id", (project_id,)
            ).fetchall()
        return [self._edge_from_row(row) for row in rows]

    def list_incident_edges(self, node_id: str) -> list[Edge]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM edges WHERE source_id = ? OR target_id = ? ORDER BY id",
                (node_id, node_id),
            ).fetchall()
        return [self._edge_from_row(row) for row in rows]

    def stats(self, project_id: str | None = None) -> dict[str, int]:
        where = " WHERE project_id = ?" if project_id else ""
        params: tuple[str, ...] = (project_id,) if project_id else ()
        with self.database.connect() as connection:
            projects = connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
            nodes = connection.execute(f"SELECT COUNT(*) FROM nodes{where}", params).fetchone()[0]
            edges = connection.execute(f"SELECT COUNT(*) FROM edges{where}", params).fetchone()[0]
        return {"projects": projects, "nodes": nodes, "edges": edges}

    @staticmethod
    def _node_values(node: Node) -> tuple[object, ...]:
        return (
            node.id,
            node.project_id,
            node.type,
            node.name,
            node.path,
            json.dumps(node.metadata, sort_keys=True),
            node.source,
            node.source_hash,
        )

    @staticmethod
    def _edge_values(edge: Edge) -> tuple[object, ...]:
        return (
            edge.id,
            edge.project_id,
            edge.source_id,
            edge.target_id,
            edge.type,
            json.dumps(edge.metadata, sort_keys=True),
        )

    @staticmethod
    def _node_from_row(row: sqlite3.Row) -> Node:
        return Node(
            id=row["id"],
            project_id=row["project_id"],
            type=row["type"],
            name=row["name"],
            path=row["path"],
            metadata=json.loads(row["metadata_json"]),
            source=row["source"],
            source_hash=row["source_hash"],
        )

    @staticmethod
    def _edge_from_row(row: sqlite3.Row) -> Edge:
        return Edge(
            id=row["id"],
            project_id=row["project_id"],
            source_id=row["source_id"],
            target_id=row["target_id"],
            type=row["type"],
            metadata=json.loads(row["metadata_json"]),
        )
