import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.articles.repository.postgres_article_repository import PostgresArticleRepository
from app.evaluation.evaluation_service import EvaluationResult, EvaluationService
from app.evaluation.repository.evaluation_repository import EvaluationRepository
from app.graph.repository.graph_repository import GraphRepository
from app.kb.prompts import PROMPTS

logger = logging.getLogger(__name__)
router = APIRouter()

_graph_repository = GraphRepository()
_article_repository = PostgresArticleRepository()
_evaluation_service = EvaluationService()
_evaluation_repository = EvaluationRepository()


class EvaluateRequest(BaseModel):
    graph_id: int
    model: str = "claude-sonnet-4-6"
    # fallback fields — used only when the graph has no linked article / prompt
    text: str | None = None
    prompt_key: str | None = None


class EvaluationSummary(BaseModel):
    id: int
    graph_id: int
    prompt_key: str
    eval_model: str
    precision: float
    recall: float
    f1: float
    supported_count: int
    unsupported_count: int
    missing_count: int
    created_at: str


@router.get("/prompts")
def get_prompts():
    result = []
    for prompt_set, types in PROMPTS.items():
        for prompt_type in types:
            result.append({
                "key": f"{prompt_set}/{prompt_type}",
                "label": f"{prompt_set} / {prompt_type}",
            })
    return result


@router.get("/evaluations", response_model=list[EvaluationSummary])
def list_evaluations():
    entities = _evaluation_repository.get_all()
    return [
        EvaluationSummary(
            id=e.id,
            graph_id=e.graph_id,
            prompt_key=e.prompt_key,
            eval_model=e.eval_model,
            precision=e.precision,
            recall=e.recall,
            f1=e.f1,
            supported_count=e.supported_count,
            unsupported_count=e.unsupported_count,
            missing_count=e.missing_count,
            created_at=e.created_at.isoformat(),
        )
        for e in entities
    ]


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationResult)
def get_evaluation(evaluation_id: int):
    entity = _evaluation_repository.get(evaluation_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Evaluation {evaluation_id} not found")
    return EvaluationResult(
        graph_id=entity.graph_id,
        graph_relations=entity.supported_count + entity.unsupported_count,
        eval_model=entity.eval_model,
        precision=entity.precision,
        recall=entity.recall,
        f1=entity.f1,
        supported_count=entity.supported_count,
        unsupported_count=entity.unsupported_count,
        missing_count=entity.missing_count,
        triple_verdicts=[
            {"triple": v.triple, "supported": v.supported, "comment": v.comment}
            for v in entity.triple_verdicts
        ],
        missing_relations=[r.relation for r in entity.missing_relations],
        analysis=entity.analysis,
    )


@router.delete("/evaluations/{evaluation_id}", status_code=204)
def delete_evaluation(evaluation_id: int):
    if not _evaluation_repository.delete(evaluation_id):
        raise HTTPException(status_code=404, detail=f"Evaluation {evaluation_id} not found")


@router.post("/evaluate", response_model=EvaluationResult)
async def evaluate(request: EvaluateRequest):
    graph = _graph_repository.get_graph(request.graph_id)
    if graph is None:
        raise HTTPException(status_code=404, detail=f"Graph {request.graph_id} not found")

    # resolve text
    text = request.text
    if not text:
        if graph.article_id is None:
            raise HTTPException(status_code=400, detail="Graph has no linked article. Provide text manually.")
        article = _article_repository.get_article(graph.article_id)
        if article is None:
            raise HTTPException(status_code=404, detail=f"Linked article {graph.article_id} not found.")
        text = article.text

    # resolve prompt key
    prompt_key = request.prompt_key or graph.prompt_key
    if not prompt_key:
        raise HTTPException(status_code=400, detail="Graph has no linked prompt. Provide prompt_key manually.")
    parts = prompt_key.split("/", 1)
    if len(parts) != 2 or parts[0] not in PROMPTS or parts[1] not in PROMPTS[parts[0]]:
        raise HTTPException(status_code=400, detail=f"Unknown prompt key: {prompt_key}")

    prompt_template = PROMPTS[parts[0]][parts[1]]
    result = await asyncio.to_thread(_evaluation_service.evaluate, graph, text, prompt_template, request.model)
    await asyncio.to_thread(_evaluation_repository.save, result, prompt_key)
    return result
