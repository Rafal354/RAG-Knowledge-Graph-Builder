import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.kb.knowledge_base_service import knowledge_base_service
from app.kb.prompt_config_service import prompt_config_service

logger = logging.getLogger(__name__)
router = APIRouter()


class CreatePromptConfigRequest(BaseModel):
    name: str
    entity_types: str = ""
    rules: str = ""
    language: str = "pl"
    examples_positive: str | None = None
    examples_negative: str | None = None
    mode: str = "structured"
    custom_content: str | None = None


class UpdatePromptConfigRequest(BaseModel):
    name: str
    entity_types: str = ""
    rules: str = ""
    language: str = "pl"
    examples_positive: str | None = None
    examples_negative: str | None = None
    mode: str = "structured"
    custom_content: str | None = None


class PromptSetRequest(BaseModel):
    key: str


@router.get("/prompt-configs")
def list_prompt_configs():
    return prompt_config_service.list_configs()


@router.post("/prompt-configs", status_code=201)
def create_prompt_config(request: CreatePromptConfigRequest):
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")
    if request.language not in ("pl", "en"):
        raise HTTPException(status_code=400, detail="Language must be 'pl' or 'en'")
    if request.mode not in ("structured", "custom"):
        raise HTTPException(status_code=400, detail="Mode must be 'structured' or 'custom'")
    if request.mode == "structured":
        if not request.entity_types.strip():
            raise HTTPException(status_code=400, detail="Entity types are required for structured mode")
        if not request.rules.strip():
            raise HTTPException(status_code=400, detail="Rules are required for structured mode")
    if request.mode == "custom" and not (request.custom_content or "").strip():
        raise HTTPException(status_code=400, detail="Custom content is required for custom mode")
    return prompt_config_service.create_config(
        name=request.name.strip(),
        entity_types=request.entity_types.strip(),
        rules=request.rules.strip(),
        language=request.language,
        examples_positive=request.examples_positive.strip() if request.examples_positive else None,
        examples_negative=request.examples_negative.strip() if request.examples_negative else None,
        mode=request.mode,
        custom_content=request.custom_content.strip() if request.custom_content else None,
    )


@router.put("/prompt-configs/{key}")
def update_prompt_config(key: str, request: UpdatePromptConfigRequest):
    config = prompt_config_service.get_config(key)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Prompt config '{key}' not found")
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")
    if request.language not in ("pl", "en"):
        raise HTTPException(status_code=400, detail="Language must be 'pl' or 'en'")
    if request.mode not in ("structured", "custom"):
        raise HTTPException(status_code=400, detail="Mode must be 'structured' or 'custom'")
    if request.mode == "structured":
        if not request.entity_types.strip():
            raise HTTPException(status_code=400, detail="Entity types are required for structured mode")
        if not request.rules.strip():
            raise HTTPException(status_code=400, detail="Rules are required for structured mode")
    if request.mode == "custom" and not (request.custom_content or "").strip():
        raise HTTPException(status_code=400, detail="Custom content is required for custom mode")
    updated = prompt_config_service.update_config(
        key=key,
        name=request.name.strip(),
        entity_types=request.entity_types.strip(),
        rules=request.rules.strip(),
        language=request.language,
        examples_positive=request.examples_positive.strip() if request.examples_positive else None,
        examples_negative=request.examples_negative.strip() if request.examples_negative else None,
        mode=request.mode,
        custom_content=request.custom_content.strip() if request.custom_content else None,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Prompt config '{key}' not found")
    return updated


@router.get("/prompt-configs/{key}/content")
def get_prompt_config_content(key: str):
    config = prompt_config_service.get_config(key)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Prompt config '{key}' not found")
    new_graph = prompt_config_service.get_prompt_content(f"{key}/new_graph")
    existing_graph = prompt_config_service.get_prompt_content(f"{key}/existing_graph")
    return {"new_graph": new_graph, "existing_graph": existing_graph}


@router.delete("/prompt-configs/{key}", status_code=204)
def delete_prompt_config(key: str):
    config = prompt_config_service.get_config(key)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Prompt config '{key}' not found")
    if config["is_builtin"]:
        raise HTTPException(status_code=400, detail="Cannot delete built-in prompt configs")
    if not prompt_config_service.delete_config(key):
        raise HTTPException(status_code=500, detail="Failed to delete prompt config")


@router.get("/prompt-set")
def get_prompt_set():
    return {"key": knowledge_base_service.prompt_service.prompt_set}


@router.put("/prompt-set", status_code=204)
def set_prompt_set(request: PromptSetRequest):
    config = prompt_config_service.get_config(request.key)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Prompt config '{request.key}' not found")
    knowledge_base_service.set_prompt_set(request.key)
