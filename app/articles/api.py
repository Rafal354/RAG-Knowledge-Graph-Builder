import logging

from fastapi import APIRouter, HTTPException

from app.api import api
from app.model.article_list_response import ArticleListResponse
from app.model.article_meta import ArticleMeta
from app.model.ingest_request import IngestRequest
from app.services.naive_graph_ingest_service import graph_ingest_service

logger = logging.getLogger(__name__)
router = APIRouter()

ARTICLE_NOT_FOUND = "Article not found"


@router.post("/articles", response_model=dict, status_code=201)
async def add_article(request: IngestRequest):
    """
    Saves a new article to the database and updates the knowledge graph
    """
    if api.builder is None:
        raise HTTPException(status_code=500, detail="Neo4j driver not initialized")

    try:
        logger.info("Trying to add new article")
        result = graph_ingest_service.add_article(request)
        logger.info("Added new article: %s", result)
        logger.info("Updating knowledge graph")
        stats = api.builder.update_graph()
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
