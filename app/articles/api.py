import logging
from typing import List

from fastapi import APIRouter, HTTPException

from app.articles.model.add_article_request import AddArticleRequest
from app.articles.model.article import Article
from app.articles.model.article_details import ArticleDetails
from app.services.article_service import article_service

logger = logging.getLogger(__name__)
router = APIRouter()

ARTICLE_NOT_FOUND = "Article not found"


@router.post("/articles", response_model=ArticleDetails, status_code=201)
async def add_article(request: AddArticleRequest):
    """
    Add an article
    :param request:
    :return:
    """
    try:
        return article_service.add_article(request)
    except Exception as e:
        logger.exception("Unexpected error during adding article: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/articles", response_model=List[ArticleDetails], status_code=200)
async def list_articles():
    """
    Get all articles metadata
    """
    return article_service.list_articles()


@router.get("/articles/{article_id}", response_model=Article, status_code=200)
async def get_article(article_id: int):
    """
    Get an article
    :param article_id:
    :return:
    """
    article = article_service.get_article(article_id)
    if not article:
        logger.warning("Article with id=%s not found", article_id)
        raise HTTPException(status_code=404, detail=ARTICLE_NOT_FOUND)
    return article


@router.delete("/articles/{article_id}", status_code=204)
async def delete_article(article_id: int):
    """
    Delete an article
    :param article_id:
    :return:
    """
    deleted = article_service.delete_article(article_id)
    if not deleted:
        logger.warning("Article with id=%s not found", article_id)
        raise HTTPException(status_code=404, detail=ARTICLE_NOT_FOUND)
