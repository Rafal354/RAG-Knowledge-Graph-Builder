import logging

from fastapi import APIRouter

from app.articles.model.article_entity import Base
from app.config.config import settings
from app.db.database import engine
from app.neo4j.neo4j_kb_builder import Neo4jKBBuilder

logger = logging.getLogger(__name__)
router = APIRouter()
builder: Neo4jKBBuilder | None = None

ARTICLE_NOT_FOUND = "Article not found"


def startup_event():
    global builder
    Base.metadata.create_all(bind=engine)
    builder = Neo4jKBBuilder(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    logger.info("Neo4j driver initialized")


def shutdown_event():
    global builder
    if builder is not None:
        builder.close()
        logger.info("Neo4j driver closed")
        builder = None


@router.get("/health", response_model=dict)
async def healthcheck():
    return {
        "status": "ok",
        "neo4j_initialized": builder is not None,
        "openai_configured": bool(settings.openai_api_key),
    }
