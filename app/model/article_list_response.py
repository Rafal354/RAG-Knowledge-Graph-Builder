from typing import List

from openai import BaseModel

from app.model.article_meta import ArticleMeta


class ArticleListResponse(BaseModel):
    items: List[ArticleMeta]