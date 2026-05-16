import asyncio
import logging

import requests
from fastapi import APIRouter
from pydantic import BaseModel

from app.kb.knowledge_base_service import knowledge_base_service

logger = logging.getLogger(__name__)
router = APIRouter()

LM_STUDIO_BASE_URL = "http://localhost:1234/v1"


class ModelRequest(BaseModel):
    model: str


@router.get("/model")
async def get_model():
    return {"model": knowledge_base_service.current_model}


@router.put("/model", status_code=204)
async def set_model(request: ModelRequest):
    knowledge_base_service.set_model(request.model)


@router.get("/status")
async def get_status():
    return knowledge_base_service.get_status()


@router.get("/local-models")
async def get_local_models():
    def _fetch():
        res = requests.get(f"{LM_STUDIO_BASE_URL}/models", timeout=2.0)
        res.raise_for_status()
        return res.json()

    try:
        data = await asyncio.to_thread(_fetch)
        models = [
            m["id"] for m in data.get("data", [])
            if "embed" not in m["id"].lower()
        ]
        return {"models": models}
    except Exception:
        logger.info("LM Studio not available at %s", LM_STUDIO_BASE_URL)
        return {"models": []}
