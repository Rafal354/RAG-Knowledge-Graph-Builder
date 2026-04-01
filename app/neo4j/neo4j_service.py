import logging

from neo4j import GraphDatabase
from neo4j import Session

from app.graph.model.graph import GraphDetails
from app.graph.repository.graph_repository import GraphRepository
from app.graph.service.graph_service import GraphService

logger = logging.getLogger(__name__)


def add_graph_to_neo4j(session: Session, graph: GraphDetails) -> tuple[int, int]:
    logger.info("Neo4j %s", graph)

    total_entities = 0
    total_relations = 0

    if graph is None:
        return 0, 0

    unique_entities = set()

    for relation in graph.relations:
        unique_entities.add(relation.entity_1)
        unique_entities.add(relation.entity_2)

    for entity_name in unique_entities:
        session.run(
            """
            MERGE (e:Entity {name: $name})
            """,
            name=entity_name,
        )
        total_entities += 1

    for relation in graph.relations:
        session.run(
            """
            MATCH (s:Entity {name: $source})
            MATCH (t:Entity {name: $target})
            CREATE (s)-[:RELATION {name: $relation}]->(t)
            """,
            source=relation.entity_1,
            target=relation.entity_2,
            relation=relation.relation,
        )
        total_relations += 1

    print("Entities: %d" % total_entities)
    print("Relations: %d" % total_relations)

    return total_entities, total_relations


def clean_database(session: Session):
    result = session.run("MATCH (n) RETURN count(n) AS c").single()
    print("Nodes before deleting:", result["c"])

    session.run("MATCH (n) DETACH DELETE n")

    session.run("MATCH (n) DETACH DELETE n")
    result = session.run("MATCH (n) RETURN count(n) AS c").single()


class Neo4jService:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.graph_service = GraphService(GraphRepository())

    def close(self):
        self.driver.close()

    def clean_database(self):
        clean_database(self.driver.session())

    def update_graph(self) -> None:
        logger.info("Neo4j")
        latest_graph = self.graph_service.get_latest_graph()
        logger.info("Neo4j done: %s", latest_graph)

        with self.driver.session() as session:
            clean_database(session)
            add_graph_to_neo4j(session, latest_graph)

    def build_specific_version(self, graph_id: int) -> None:
        logger.info("Neo4j")
        graph = self.graph_service.get_graph(graph_id)
        logger.info("Neo4j done: %s", graph)

        with self.driver.session() as session:
            clean_database(session)
            add_graph_to_neo4j(session, graph)
