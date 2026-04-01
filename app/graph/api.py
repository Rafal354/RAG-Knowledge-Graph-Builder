import logging

from fastapi import APIRouter

from app.graph.repository.graph_repository import GraphRepository
from app.graph.service.graph_service import GraphService
from app.kb.knowledge_base_service import knowledge_base_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/graphs/{graph_id}", status_code=201)
async def build_specific_version(graph_id: int):
    return knowledge_base_service.build_specific_version(graph_id)


@router.get("/graphs", status_code=200)  ## response_model=GraphDetails | None
async def get_latest_graph():
    logger.info(f"Getting graph with id={"latest"}")
    return GraphService(GraphRepository()).get_latest_graph()


@router.get("/graphs/{graph_id}", status_code=200)  ## response_model=GraphDetails | None
async def get_graph(graph_id: int):
    logger.info(f"Getting graph with id={graph_id}")
    return GraphService(GraphRepository()).get_graph(graph_id)


@router.delete("/graphs/clean", status_code=204)
async def clean_graph():
    print("Deleting graph")
    knowledge_base_service.clear_knowledge_base()
