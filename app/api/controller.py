import logging
import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.model.article_list_response import ArticleListResponse
from app.model.article_meta import ArticleMeta
from app.model.ingest_request import IngestRequest
from app.neo4j.neo4j_kb_builder import Neo4jKBBuilder
from app.services.naive_graph_ingest_service import graph_ingest_service

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
router = APIRouter()
builder: Neo4jKBBuilder | None = None
load_dotenv()


def startup_event():
    global builder
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


@router.get("/health")
async def healthcheck():
    print(f"OpenAI API key: {os.getenv('OPENAI_API_KEY')}")
    return {"status": "ok"}


@router.post("/articles", response_model=dict)
async def add_article(payload: IngestRequest):
    """
    Saves the new article and updates knowledge base graf base on kb.txt file
    """
    global builder
    if builder is None:
        raise HTTPException(status_code=500, detail="Neo4j driver not initialized")

    try:
        print("Try to add new article")
        result = graph_ingest_service.add_article(payload)
        print(f"Added new article: {result}")
        stats = builder.update_graph()
        print("Graph built from KB file: %s", stats)

    except Exception as e:
        logger.exception("Error during adding article")
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "ok", "database": result}


@router.get("/articles", response_model=ArticleListResponse)
async def list_articles():
    """
    Get all articles metadata
    """
    items = graph_ingest_service.list_articles()
    return ArticleListResponse(items=[ArticleMeta(**m) for m in items])


@router.get("/articles/{article_id}")
async def get_article(article_id: int):
    article = graph_ingest_service.get_article(article_id)
    if not article:
        raise HTTPException(404, "Article not found")
    return article


@router.delete("/articles/{article_id}")
async def delete_article(article_id: int):
    deleted = graph_ingest_service.delete_article(article_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Article not found")

    return {"status": "ok", "message": f"Article {article_id} deleted"}
