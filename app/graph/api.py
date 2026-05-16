import logging

from fastapi import APIRouter
from pydantic import BaseModel

from app.graph.repository.graph_repository import GraphRepository
from app.graph.service.graph_service import GraphService
from app.kb.knowledge_base_service import knowledge_base_service

logger = logging.getLogger(__name__)
router = APIRouter()

_graph_service = GraphService(GraphRepository())


class ManualGraphRequest(BaseModel):
    title: str = "manual"
    relations_text: str


@router.post("/graphs/manual", status_code=201)
async def create_manual_graph(request: ManualGraphRequest):
    formatted = "[RELATIONS]\n" + request.relations_text
    return _graph_service.save_graph(formatted, title=request.title, model="manual")


@router.post("/graphs/{graph_id}", status_code=201)
async def build_specific_version(graph_id: int):
    return knowledge_base_service.build_specific_version(graph_id)


@router.get("/graphs", status_code=200)  ## response_model=GraphDetails | None
async def get_latest_graph():
    logger.info("Getting latest graph")
    return _graph_service.get_latest_graph()


@router.get("/graphs/all", status_code=200)
async def get_all_graphs():
    try:
        return _graph_service.get_all_graphs()
    except Exception:
        logger.exception("Failed to fetch graph list")
        return []


@router.get("/graphs/{graph_id}", status_code=200)  ## response_model=GraphDetails | None
async def get_graph(graph_id: int):
    logger.info("Getting graph with id=%s", graph_id)
    return _graph_service.get_graph(graph_id)


class PatchGraphRequest(BaseModel):
    position: int


@router.patch("/graphs/{graph_id}", status_code=204)
async def patch_graph(graph_id: int, request: PatchGraphRequest):
    from fastapi import HTTPException
    if not _graph_service.update_graph_position(graph_id, request.position):
        raise HTTPException(status_code=404, detail="Graph not found")


@router.delete("/graphs/clean", status_code=204)
async def clean_graph():
    knowledge_base_service.clear_knowledge_base()


@router.delete("/graphs/{graph_id}", status_code=204)
async def delete_graph(graph_id: int):
    deleted = _graph_service.delete_graph(graph_id)
    if not deleted:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Graph not found")
