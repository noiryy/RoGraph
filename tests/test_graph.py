from pathlib import Path

from roblox_graph.graph.engine import GraphEngine
from roblox_graph.graph.intelligence import GraphIntelligence
from roblox_graph.models.edge import Edge
from roblox_graph.models.node import Node
from roblox_graph.models.project import Project
from roblox_graph.storage.database import Database
from roblox_graph.storage.repositories import GraphRepository


def make_graph(tmp_path: Path) -> tuple[GraphRepository, GraphEngine]:
    database = Database(tmp_path / "graph.db")
    database.initialize()
    repository = GraphRepository(database)
    repository.upsert_project(Project(id="place-1", name="Example"))
    return repository, GraphEngine(repository)


def test_dependencies_and_shortest_path_are_directed(tmp_path: Path) -> None:
    repository, graph = make_graph(tmp_path)
    controller = Node.create(
        project_id="place-1", type="LocalScript", name="Controller", path="StarterPlayer.Controller"
    )
    remote = Node.create(
        project_id="place-1",
        type="RemoteEvent",
        name="Purchase",
        path="ReplicatedStorage.Purchase",
    )
    service = Node.create(
        project_id="place-1",
        type="ModuleScript",
        name="Service",
        path="ServerScriptService.Service",
    )
    for node in (controller, remote, service):
        repository.upsert_node(node)
    repository.upsert_edge(
        Edge.create(
            project_id="place-1", source_id=controller.id, target_id=remote.id, type="FIRES"
        )
    )
    repository.upsert_edge(
        Edge.create(
            project_id="place-1", source_id=remote.id, target_id=service.id, type="LISTENS_TO"
        )
    )

    assert [node.name for node in graph.get_dependencies(controller.id, depth=2)] == [
        "Purchase",
        "Service",
    ]
    assert [node.name for node in graph.get_dependents(service.id)] == ["Purchase"]
    assert [node.name for node in graph.shortest_path(controller.id, service.id)] == [
        "Controller",
        "Purchase",
        "Service",
    ]


def test_node_ids_are_stable_and_storage_is_persistent(tmp_path: Path) -> None:
    repository, _ = make_graph(tmp_path)
    node = Node.create(
        project_id="place-1",
        type="ModuleScript",
        name="Inventory",
        path="ServerScriptService.Inventory",
    )
    assert (
        node.id
        == Node.create(
            project_id="place-1",
            type="ModuleScript",
            name="Inventory",
            path="ServerScriptService.Inventory",
        ).id
    )
    repository.upsert_node(node)

    reopened = GraphRepository(Database(tmp_path / "graph.db"))
    assert reopened.get_node(node.id) == node


def test_intelligence_ranks_coupled_nodes_and_summarizes_communities(tmp_path: Path) -> None:
    repository, _ = make_graph(tmp_path)
    controller = Node.create(
        project_id="place-1", type="LocalScript", name="Controller", path="StarterPlayer.Controller"
    )
    remote = Node.create(
        project_id="place-1",
        type="RemoteEvent",
        name="Purchase",
        path="ReplicatedStorage.Purchase",
    )
    service = Node.create(
        project_id="place-1",
        type="Script",
        name="Service",
        path="ServerScriptService.Service",
    )
    isolated = Node.create(project_id="place-1", type="Folder", name="Isolated", path="Workspace")
    for node in (controller, remote, service, isolated):
        repository.upsert_node(node)
    repository.upsert_edge(
        Edge.create(
            project_id="place-1", source_id=controller.id, target_id=remote.id, type="FIRES"
        )
    )
    repository.upsert_edge(
        Edge.create(
            project_id="place-1", source_id=remote.id, target_id=service.id, type="LISTENS_TO"
        )
    )

    intelligence = GraphIntelligence(repository)
    overview = intelligence.overview("place-1")
    god_nodes = intelligence.god_nodes("place-1")

    assert overview["community_count"] == 1
    assert overview["isolated_node_count"] == 1
    assert overview["architecture_areas"][0]["node_count"] == 3
    assert god_nodes[0]["name"] == "Purchase"
    assert god_nodes[0]["coupling_score"] > 0
