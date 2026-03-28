import logging

from fastapi import APIRouter

from app.graph.model.graph import GraphDetails
from app.graph.repository.graph_repository import GraphRepository
from app.kb.knowledge_base_service import knowledge_base_service
from app.graph.service.graph_service import GraphService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/graphs", status_code=200)  ## response_model=GraphDetails | None
async def get_latest_graph():
    return GraphService(GraphRepository()).get_latest_graph()


@router.delete("/graphs/clean", status_code=204)
async def delete_graph():
    print("Deleting graph")
    knowledge_base_service.clear_knowledge_base()
