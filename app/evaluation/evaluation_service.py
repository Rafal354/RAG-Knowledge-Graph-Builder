import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class EvaluationResult(BaseModel):
    graph_id: int
    graph_relations: int
    analysis: str


def _graph_to_text(graph) -> str:
    return "\n".join(
        f"{r.entity_1} -> {r.relation} -> {r.entity_2}"
        for r in graph.relations
    )


class EvaluationService:

    def evaluate(self, graph, text: str, prompt_template: str) -> EvaluationResult:
        from langchain.chat_models import init_chat_model

        graph_text = _graph_to_text(graph)

        prompt = (
            f"You are evaluating a knowledge graph extracted from a text.\n\n"
            f"The extraction prompt used to create this graph was:\n{prompt_template}\n\n"
            f"Source text:\n{text}\n\n"
            f"Knowledge graph ({len(graph.relations)} relations):\n{graph_text}\n\n"
            f"Taking into account the intent of the extraction prompt, assess how well the knowledge graph "
            f"captures the information in the source text. Report:\n"
            f"- Precision: fraction of graph relations that are actually supported by the text\n"
            f"- Recall: fraction of important relations in the text that are captured in the graph\n"
            f"- F1 score\n"
            f"- Brief analysis of what is missing, what is incorrect, and what is well captured"
        )

        llm = init_chat_model("claude-sonnet-4-6", timeout=120)
        response = llm.invoke(prompt)

        return EvaluationResult(
            graph_id=graph.id,
            graph_relations=len(graph.relations),
            analysis=response.content.strip(),
        )
