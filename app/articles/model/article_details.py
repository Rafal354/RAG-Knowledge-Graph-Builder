from datetime import datetime

from pydantic import BaseModel, Field

from app.articles.model.article_entity import ArticleEntity


class ArticleDetails(BaseModel):
    article_id: int = Field(..., description="Unique article identifier")
    title: str = Field(..., description="Article title")
    created_at: datetime = Field(..., description="Article creation timestamp")
    text_length: int = Field(..., description="Length of article text")

    @classmethod
    def from_entity(cls, article: ArticleEntity):
        return cls(
            article_id=article.id,
            title=article.title,
            created_at=article.created_at,
            text_length=article.text_length,
        )
