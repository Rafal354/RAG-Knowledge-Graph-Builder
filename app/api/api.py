import logging

from fastapi import APIRouter

from app.articles.model.article_entity import Base
from app.config.database import engine
from app.config.settings import settings
from app.neo4j.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)
router = APIRouter()
neo4j_service: Neo4jService | None = None

ARTICLE_NOT_FOUND = "Article not found"


def startup_event():
    Base.metadata.create_all(bind=engine)
    global neo4j_service
    neo4j_service = Neo4jService(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    logger.info("Neo4j driver initialized")


def shutdown_event():
    global neo4j_service
    if neo4j_service is not None:
        neo4j_service.close()
        logger.info("Neo4j driver closed")
        neo4j_service = None


@router.get("/health", response_model=dict)
async def healthcheck():
    return {
        "status": "ok",
        "neo4j_initialized": neo4j_service is not None,
        "openai_configured": bool(settings.openai_api_key),
    }
