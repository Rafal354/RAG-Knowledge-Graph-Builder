import logging

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.model.article_list_response import ArticleListResponse
from app.model.article_meta import ArticleMeta
from app.model.ingest_request import IngestRequest
from app.neo4j.neo4j_kb_builder import Neo4jKBBuilder
from app.services.naive_graph_ingest_service import graph_ingest_service

logger = logging.getLogger(__name__)
router = APIRouter()
builder: Neo4jKBBuilder | None = None

ARTICLE_NOT_FOUND = "Article not found"


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


@router.get("/health", response_model=dict)
async def healthcheck():
    return {
        "status": "ok",
        "neo4j_initialized": builder is not None,
        "openai_configured": bool(settings.openai_api_key),
    }


@router.post("/articles", response_model=dict, status_code=201)
async def add_article(request: IngestRequest):
    """
    Saves a new article to the database and updates the knowledge graph
    """
    if builder is None:
        raise HTTPException(status_code=500, detail="Neo4j driver not initialized")

    try:
        logger.info("Trying to add new article")
        result = graph_ingest_service.add_article(request)
        logger.info("Added new article: %s", result)
        logger.info("Updating knowledge graph")
        stats = builder.update_graph()
        logger.info("Graph built successfully stats: %s", stats)

    except Exception as e:
        logger.exception("Error during adding article")
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "ok", "database": result}


@router.get("/articles", response_model=ArticleListResponse)
async def list_articles():
    """
    Get all articles metadata
    """
    logger.info("Listing all articles")
    items = graph_ingest_service.list_articles()
    return ArticleListResponse(items=[ArticleMeta(**item) for item in items])


@router.get("/articles/{article_id}")
async def get_article(article_id: int):
    logger.info("Getting article with id=%s", article_id)
    article = graph_ingest_service.get_article(article_id)
    if not article:
        logger.warning("Article with id=%s not found", article_id)
        raise HTTPException(status_code=404, detail=ARTICLE_NOT_FOUND)
    return article


@router.delete("/articles/{article_id}")
async def delete_article(article_id: int):
    deleted = graph_ingest_service.delete_article(article_id)
    if not deleted:
        logger.warning("Article with id=%s not found", article_id)
        raise HTTPException(status_code=404, detail=ARTICLE_NOT_FOUND)

    logger.info("Deleted article with id=%s", article_id)
    return {"status": "ok", "message": f"Article {article_id} deleted"}
