from typing import List, Optional

from app.articles.dto.add_article_request import AddArticleRequest
from app.articles.model.article import Article
from app.articles.model.article_details import ArticleDetails
from app.articles.repository.postgres_article_repository import PostgresArticleRepository
from app.articles.repository.simple_article_repository import ArticleRepository
from app.services.knowledge_base_service import knowledge_base_service


class ArticleService:
    def __init__(self, repo: ArticleRepository):
        self.repo = repo

    def add_article(self, req: AddArticleRequest) -> ArticleDetails:
        article_details = self.repo.save_article(req.title, req.text)
        knowledge_base_service.update_fun(req)
        return article_details

    def list_articles(self) -> List[ArticleDetails]:
        return self.repo.list_articles()

    def get_article(self, article_id: int) -> Optional[Article]:
        return self.repo.get_article(article_id)

    def delete_article(self, article_id: int) -> bool:
        return self.repo.delete_article(article_id)



article_service = ArticleService(PostgresArticleRepository())
