from typing import List, Optional

from sqlalchemy import select

from app.articles.model.article import Article
from app.articles.model.article_details import ArticleDetails
from app.articles.model.article_entity import ArticleEntity
from app.articles.repository.article_repository import ArticleRepository
from app.db.database import SessionLocal


class PostgresArticleRepository(ArticleRepository):
    def save_article(self, title: str, text: str) -> ArticleDetails:
        with SessionLocal() as session:
            article = ArticleEntity(
                title=title,
                text=text,
                text_length=len(text),
            )
            session.add(article)
            session.commit()
            session.refresh(article)

            return ArticleDetails.from_entity(article)

    def list_articles(self) -> List[ArticleDetails]:
        with SessionLocal() as session:
            stmt = select(ArticleEntity).order_by(ArticleEntity.id.asc())
            articles = session.scalars(stmt).all()
            return [ArticleDetails.from_entity(article) for article in articles]

    def get_article(self, article_id: int) -> Optional[Article]:
        with SessionLocal() as session:
            article = session.get(ArticleEntity, article_id)
            return Article.from_entity(article) if article else None

    def delete_article(self, article_id: int) -> bool:
        with SessionLocal() as session:
            article = session.get(ArticleEntity, article_id)
            if article is None:
                return False

            session.delete(article)
            session.commit()
            return True
