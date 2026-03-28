import logging

from fastapi import APIRouter
from app.kb.knowledge_base_service import knowledge_base_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.delete("/graphs/clean", status_code=204)
async def delete_graph():
    print("Deleting graph")
    knowledge_base_service.clear_knowledge_base()
