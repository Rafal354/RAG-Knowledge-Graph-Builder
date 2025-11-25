from pathlib import Path
from typing import Dict, Any

from neo4j import GraphDatabase, Session

from app.parser.knowledge_base_parser import parse, KBParsed

BASE_DIR = Path(__file__).resolve().parent.parent.parent / "database"
ENTITIES_FILE = BASE_DIR / "entities.txt"
RELATIONS_FILE = BASE_DIR / "relations.txt"

def add_entities_and_relations(session: Session, parsed: KBParsed):
    total_entities = 0
    total_relations = 0

    for entity in parsed.entities:
        session.run(
            """
            MERGE (e:Entity {name: $name})
            """,
            name=entity,
        )
        total_entities += 1

    for relation in parsed.relations:
        # print("RELATION:", rel.source, rel.relation, rel.target)
        session.run(
            """
            MATCH (s:Entity {name: $source})
            MATCH (t:Entity {name: $target})
            CREATE (s)-[:RELATION {name: $relation}]->(t)
            """,
            source=relation.source,
            target=relation.target,
            relation=relation.relation,
        )
        total_relations += 1

    return total_entities, total_relations


def clean_database(session: Session):
    result = session.run("MATCH (n) RETURN count(n) AS c").single()
    print("Nodes before deleting:", result["c"])

    session.run("MATCH (n) DETACH DELETE n")

    session.run("MATCH (n) DETACH DELETE n")
    result = session.run("MATCH (n) RETURN count(n) AS c").single()
    print("Nodes after deleting:", result["c"])


class Neo4jKBBuilder:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def update_graph(self) -> Dict[str, Any]:
        parsed = parse(ENTITIES_FILE.read_text(encoding="utf-8"), RELATIONS_FILE.read_text(encoding="utf-8"))

        with self.driver.session() as session:
            clean_database(session)
            entities, relations = add_entities_and_relations(session, parsed)

        return {
            "entities_total": entities,
            "relations_total": relations,
        }
