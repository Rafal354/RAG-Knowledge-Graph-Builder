import logging

from fastapi import APIRouter
from pydantic import BaseModel

from app.kb.knowledge_base_service import knowledge_base_service

logger = logging.getLogger(__name__)
router = APIRouter()


class ModelRequest(BaseModel):
    model: str


@router.get("/model")
async def get_model():
    return {"model": knowledge_base_service.current_model}


@router.put("/model", status_code=204)
async def set_model(request: ModelRequest):
    knowledge_base_service.set_model(request.model)
