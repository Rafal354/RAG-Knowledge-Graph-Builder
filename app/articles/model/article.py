from pydantic import Field

from app.articles.model.article_details import ArticleDetails
from app.articles.model.article_entity import ArticleEntity


class Article(ArticleDetails):
    text: str = Field(..., description="Article text")

    @classmethod
    def from_entity(cls, article: ArticleEntity):
        return cls(
            article_id=article.id,
            title=article.title,
            created_at=article.created_at,
            text_length=article.text_length,
            text=article.text,
        )
