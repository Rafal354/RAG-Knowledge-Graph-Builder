from dataclasses import dataclass


@dataclass
class FakeRelation:
    entity_1: str
    relation: str
    entity_2: str


@dataclass
class FakeGraph:
    version: int
    relations: list[FakeRelation]
    title: str | None = None
    model: str | None = None
    article_id: int | None = None
    prompt_key: str | None = None


class FakeGraphRepository:
    """In-memory stand-in for GraphRepository, avoiding any real DB access in tests."""

    def __init__(self) -> None:
        self.graphs: list[FakeGraph] = []

    def get_latest_graph(self) -> FakeGraph | None:
        return self.graphs[-1] if self.graphs else None

    def save_graph(self, relations, title=None, model=None, article_id=None, prompt_key=None) -> FakeGraph:
        graph = FakeGraph(
            version=len(self.graphs) + 1,
            relations=[FakeRelation(*relation) for relation in relations],
            title=title,
            model=model,
            article_id=article_id,
            prompt_key=prompt_key,
        )
        self.graphs.append(graph)
        return graph


def relation_set(graph: FakeGraph) -> set[tuple[str, str, str]]:
    return {(r.entity_1, r.relation, r.entity_2) for r in graph.relations}
