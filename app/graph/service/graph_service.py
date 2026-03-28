import logging

from app.graph.model.graph import GraphDetails
from app.graph.repository.graph_repository import GraphRepository

logger = logging.getLogger(__name__)


class GraphService:
    def __init__(self, graph_repository: GraphRepository) -> None:
        self.graph_repository = graph_repository

    def save_graph(self, llm_output: str) -> GraphDetails:
        relations = self._parse_relations(llm_output)
        logger.info(f"Relations: {relations}")
        return self.graph_repository.save_graph(relations)

    def get_latest_graph_text(self) -> str:
        latest_graph = self.graph_repository.get_latest_graph()
        return self.build_graph_text(latest_graph)

    def get_latest_graph(self) -> GraphDetails | None:
        return self.graph_repository.get_latest_graph()

    def build_graph_text(self, graph) -> str:
        if graph is None:
            return ""

        lines = ["[RELATIONS]"]
        for rel in graph.relations:
            lines.append(f"{rel.entity_1} -> {rel.relation} -> {rel.entity_2}")

        return "\n".join(lines)

    @staticmethod
    def _parse_relations(llm_output: str) -> list[tuple[str, str, str]]:
        if llm_output is None or llm_output == "":
            return []
        relations = llm_output.split("\n")
        parts = llm_output.split("[RELATIONS]", maxsplit=1)
        if len(parts) < 2:
            return []

        relations_part = parts[1].strip()
        relations: list[tuple[str, str, str]] = []

        for line in relations_part.splitlines():
            line = line.strip()
            if not line:
                continue

            chunks = [part.strip() for part in line.split("->")]
            if len(chunks) != 3:
                continue

            entity_1, relation, entity_2 = chunks
            relations.append((entity_1, relation, entity_2))

        return relations
