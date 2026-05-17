import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.evaluation.evaluation_service import EvaluationResult, EvaluationService
from app.graph.repository.graph_repository import GraphRepository
from app.kb.prompts import PROMPTS

logger = logging.getLogger(__name__)
router = APIRouter()

_graph_repository = GraphRepository()
_evaluation_service = EvaluationService()


class EvaluateRequest(BaseModel):
    graph_id: int
    text: str
    prompt_key: str  # format: "default_en/new_graph"


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


@router.post("/evaluate", response_model=EvaluationResult)
async def evaluate(request: EvaluateRequest):
    graph = _graph_repository.get_graph(request.graph_id)
    if graph is None:
        raise HTTPException(status_code=404, detail=f"Graph {request.graph_id} not found")

    parts = request.prompt_key.split("/", 1)
    if len(parts) != 2 or parts[0] not in PROMPTS or parts[1] not in PROMPTS[parts[0]]:
        raise HTTPException(status_code=400, detail=f"Unknown prompt key: {request.prompt_key}")

    prompt_template = PROMPTS[parts[0]][parts[1]]
    return await asyncio.to_thread(_evaluation_service.evaluate, graph, request.text, prompt_template)
