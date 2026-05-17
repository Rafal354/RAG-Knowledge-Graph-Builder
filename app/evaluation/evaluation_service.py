import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TripleVerdict(BaseModel):
    triple: str
    supported: bool
    comment: str | None = None


class JudgeOutput(BaseModel):
    triple_verdicts: list[TripleVerdict]
    missing_important_relations: list[str]
    analysis: str


class EvaluationResult(BaseModel):
    graph_id: int
    graph_relations: int
    precision: float
    recall: float
    f1: float
    supported_count: int
    unsupported_count: int
    missing_count: int
    triple_verdicts: list[dict]
    missing_relations: list[str]
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
            f"You are evaluating a knowledge graph extracted from a source text.\n\n"
            f"The extraction prompt used to create this graph was:\n{prompt_template}\n\n"
            f"Source text:\n{text}\n\n"
            f"Knowledge graph triples ({len(graph.relations)} total):\n{graph_text}\n\n"
            f"Your tasks:\n"
            f"1. For each triple in the graph, decide whether it is semantically supported by the source text "
            f"(supported=true) or not (hallucinated/incorrect, supported=false). "
            f"Use semantic matching — paraphrases count as supported.\n"
            f"2. List important relations present in the source text that are NOT captured by any triple in the graph. "
            f"Only include genuinely important information, not minor details.\n"
            f"3. Write a brief analysis of the overall quality.\n\n"
            f"Evaluate all {len(graph.relations)} triples."
        )

        llm = init_chat_model("claude-sonnet-4-6", timeout=120)
        judge: JudgeOutput = llm.with_structured_output(JudgeOutput).invoke(prompt)

        supported = sum(1 for v in judge.triple_verdicts if v.supported)
        unsupported = len(judge.triple_verdicts) - supported
        missing = len(judge.missing_important_relations)

        precision = supported / len(judge.triple_verdicts) if judge.triple_verdicts else 0.0
        recall = supported / (supported + missing) if (supported + missing) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        return EvaluationResult(
            graph_id=graph.id,
            graph_relations=len(graph.relations),
            precision=round(precision, 3),
            recall=round(recall, 3),
            f1=round(f1, 3),
            supported_count=supported,
            unsupported_count=unsupported,
            missing_count=missing,
            triple_verdicts=[v.model_dump() for v in judge.triple_verdicts],
            missing_relations=judge.missing_important_relations,
            analysis=judge.analysis,
        )
