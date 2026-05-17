import logging
import os
import threading
import webbrowser

from fastapi import APIRouter

from app.articles.model.article_entity import Base
import app.evaluation.model.evaluation_entity  # noqa: F401 — registers evaluation tables with Base
from app.config.database import engine
from app.config.settings import settings
from app.kb.knowledge_base_service import knowledge_base_service
from app.neo4j.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)
router = APIRouter()
neo4j_service: Neo4jService | None = None

ARTICLE_NOT_FOUND = "Article not found"


def startup_event():
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        from sqlalchemy import text
        conn.execute(text("ALTER TABLE graphs ADD COLUMN IF NOT EXISTS title TEXT"))
        conn.execute(text("ALTER TABLE graphs ADD COLUMN IF NOT EXISTS model TEXT"))
        conn.commit()
    global neo4j_service
    neo4j_service = Neo4jService(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    knowledge_base_service.neo4j_service = neo4j_service
    logger.info("Neo4j driver initialized")
    if not os.path.exists("/.dockerenv"):
        frontend_url = "http://localhost:8000"
        logger.info("Frontend available at: %s", frontend_url)
        threading.Timer(1.5, webbrowser.open, args=[frontend_url]).start()


def shutdown_event():
    knowledge_base_service.shutdown()
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
