import logging

from app.graph.model.graph import GraphDetails, GraphSummary
from app.graph.repository.graph_repository import GraphRepository

logger = logging.getLogger(__name__)


class GraphService:
    def __init__(self, graph_repository: GraphRepository) -> None:
        self.graph_repository = graph_repository

    def save_graph(self, llm_output: str, title: str | None = None, model: str | None = None, article_id: int | None = None, prompt_key: str | None = None) -> GraphDetails:
        relations = self._parse_relations(llm_output)
        logger.info("Relations: %s", relations)
        return self.graph_repository.save_graph(relations, title=title, model=model, article_id=article_id, prompt_key=prompt_key)

    def get_latest_graph_text(self) -> str:
        latest_graph = self.graph_repository.get_latest_graph()
        return self.build_graph_text(latest_graph)

    def get_all_graphs(self) -> list[GraphSummary]:
        return self.graph_repository.get_all_graphs()

    def get_latest_graph(self) -> GraphDetails | None:
        return self.graph_repository.get_latest_graph()

    def get_graph(self, graph_id: int) -> GraphDetails | None:
        return self.graph_repository.get_graph(graph_id)

    def update_graph_position(self, graph_id: int, position: int) -> bool:
        return self.graph_repository.update_graph_position(graph_id, position)

    def delete_graph(self, graph_id: int) -> bool:
        return self.graph_repository.delete_graph(graph_id)

    def build_graph_text(self, graph) -> str:
        if graph is None:
            return ""

        lines = ["[RELATIONS]"]
        for rel in graph.relations:
            lines.append(f"{rel.entity_1} -> {rel.relation} -> {rel.entity_2}")

        return "\n".join(lines)

    @staticmethod
    def _parse_relations(llm_output: str) -> list[tuple[str, str, str]]:
        if not llm_output:
            return []
        relations_part = None
        for marker in ("[RELATIONS]", "[RELACJE]"):
            if marker in llm_output:
                relations_part = llm_output.split(marker, maxsplit=1)[1].strip()
                break
        if relations_part is None:
            return []

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
