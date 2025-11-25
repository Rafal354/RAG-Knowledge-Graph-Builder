from abc import ABC, abstractmethod
from typing import List, Optional, Dict


class ArticleRepository(ABC):

    @abstractmethod
    def save_article(self, title: str, text: str) -> Dict:
        pass

    @abstractmethod
    def get_article(self, article_id: int) -> Optional[Dict]:
        pass

    @abstractmethod
    def list_articles(self) -> List[Dict]:
        pass

    @abstractmethod
    def delete_article(self, article_id: int) -> bool:
        pass
