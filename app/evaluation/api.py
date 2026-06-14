import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.articles.repository.postgres_article_repository import PostgresArticleRepository
from app.evaluation.evaluation_service import EvaluationResult, EvaluationService, build_judge_prompt
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
    reference_graph_id: int | None = None
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
    connectivity_score: float | None = None
    reference_graph_id: int | None = None
    t_precision: float | None = None
    t_recall: float | None = None
    t_f1: float | None = None
    hallucination_rate: float | None = None
    omission_rate: float | None = None
    ged: int | None = None
    matched_count: int | None = None
    reference_relation_count: int | None = None
    judge_prompt_version: int | None = None


@router.get("/prompts")
def get_prompts():
    from app.kb.prompt_config_service import prompt_config_service
    seen = set()
    result = []
    for prompt_set, types in PROMPTS.items():
        for prompt_type in types:
            key = f"{prompt_set}/{prompt_type}"
            seen.add(key)
            result.append({"key": key, "label": f"{prompt_set} / {prompt_type}"})
    for config in prompt_config_service.list_configs():
        if not config["is_builtin"]:
            for prompt_type in ("new_graph", "existing_graph"):
                key = f"{config['key']}/{prompt_type}"
                if key not in seen:
                    result.append({"key": key, "label": f"{config['name']} / {prompt_type}"})
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
            connectivity_score=e.connectivity_score,
            reference_graph_id=e.reference_graph_id,
            t_precision=e.t_precision,
            t_recall=e.t_recall,
            t_f1=e.t_f1,
            hallucination_rate=e.hallucination_rate,
            omission_rate=e.omission_rate,
            ged=e.ged,
            matched_count=e.matched_count,
            reference_relation_count=e.reference_relation_count,
            judge_prompt_version=e.judge_prompt_version,
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
        connectivity_score=entity.connectivity_score,
        reference_graph_id=entity.reference_graph_id,
        t_precision=entity.t_precision,
        t_recall=entity.t_recall,
        t_f1=entity.t_f1,
        hallucination_rate=entity.hallucination_rate,
        omission_rate=entity.omission_rate,
        ged=entity.ged,
        matched_count=entity.matched_count,
        reference_relation_count=entity.reference_relation_count,
        judge_prompt_version=entity.judge_prompt_version,
        judge_prompt_text=entity.judge_prompt_text,
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
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail=f"Invalid prompt key format: {prompt_key}")
    prompt_set, prompt_type = parts
    if prompt_set in PROMPTS and prompt_type in PROMPTS[prompt_set]:
        prompt_template = PROMPTS[prompt_set][prompt_type]
    else:
        from app.kb.prompt_config_service import prompt_config_service
        prompt_template = prompt_config_service.get_prompt_content(prompt_key)
        if prompt_template is None:
            raise HTTPException(status_code=400, detail=f"Unknown prompt key: {prompt_key}")

    reference_graph = None
    if request.reference_graph_id is not None:
        reference_graph = _graph_repository.get_graph(request.reference_graph_id)
        if reference_graph is None:
            raise HTTPException(status_code=404, detail=f"Reference graph {request.reference_graph_id} not found")
    result = await asyncio.to_thread(
        _evaluation_service.evaluate, graph, text, prompt_template, request.model, reference_graph
    )
    await asyncio.to_thread(_evaluation_repository.save, result, prompt_key)
    return result


def _resolve_prompt_template_for_backfill(prompt_key: str) -> str | None:
    parts = prompt_key.split("/", 1)
    if len(parts) != 2:
        return None
    prompt_set, prompt_type = parts
    if prompt_set in PROMPTS and prompt_type in PROMPTS[prompt_set]:
        return PROMPTS[prompt_set][prompt_type]
    from app.kb.prompt_config_service import prompt_config_service
    return prompt_config_service.get_prompt_content(prompt_key)


def backfill_judge_prompt_text() -> None:
    for e in _evaluation_repository.get_all():
        if e.judge_prompt_version != 2 or e.judge_prompt_text is not None:
            continue
        graph = _graph_repository.get_graph(e.graph_id)
        if graph is None or graph.article_id is None:
            continue
        article = _article_repository.get_article(graph.article_id)
        if article is None:
            continue
        prompt_template = _resolve_prompt_template_for_backfill(e.prompt_key)
        if prompt_template is None:
            continue
        prompt = build_judge_prompt(graph, article.text, prompt_template)
        _evaluation_repository.update_judge_prompt_text(e.id, prompt)
        logger.info("Backfilled judge_prompt_text for evaluation id=%d", e.id)
