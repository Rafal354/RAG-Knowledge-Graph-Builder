from abc import ABC, abstractmethod
from typing import List, Optional

from app.articles.model.article import Article
from app.articles.model.article_details import ArticleDetails


class ArticleRepository(ABC):

    @abstractmethod
    def save_article(self, title: str, text: str) -> ArticleDetails:
        pass

    @abstractmethod
    def list_articles(self) -> List[ArticleDetails]:
        pass

    @abstractmethod
    def get_article(self, article_id: int) -> Optional[Article]:
        pass

    @abstractmethod
    def delete_article(self, article_id: int) -> bool:
        pass
