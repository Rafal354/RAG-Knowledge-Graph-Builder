from typing import List, Optional, Dict

from sqlalchemy import select

from app.db.repository.article_repository import ArticleRepository
from app.db.database import SessionLocal
from app.db.model.article_model import ArticleEntity


class PostgresArticleRepository(ArticleRepository):
    def save_article(self, title: str, text: str) -> Dict:
        with SessionLocal() as session:
            article = ArticleEntity(
                title=title,
                text=text,
                text_length=len(text),
            )
            session.add(article)
            session.commit()
            session.refresh(article)

            return self._to_dict(article)

    def get_article(self, article_id: int) -> Optional[Dict]:
        with SessionLocal() as session:
            article = session.get(ArticleEntity, article_id)
            if article is None:
                return None
            return self._to_dict(article)

    def list_articles(self) -> List[Dict]:
        with SessionLocal() as session:
            stmt = select(ArticleEntity).order_by(ArticleEntity.id.asc())
            articles = session.scalars(stmt).all()
            return [self._to_meta_dict(article) for article in articles]

    def delete_article(self, article_id: int) -> bool:
        with SessionLocal() as session:
            article = session.get(ArticleEntity, article_id)
            if article is None:
                return False

            session.delete(article)
            session.commit()
            return True

    @staticmethod
    def _to_dict(article: ArticleEntity) -> Dict:
        return {
            "article_id": article.id,
            "title": article.title,
            "created_at": article.created_at.isoformat() if article.created_at else None,
            "text_length": article.text_length,
            "text": article.text,
        }

    @staticmethod
    def _to_meta_dict(article: ArticleEntity) -> Dict:
        return {
            "article_id": article.id,
            "title": article.title,
            "created_at": article.created_at.isoformat() if article.created_at else None,
            "text_length": article.text_length,
        }