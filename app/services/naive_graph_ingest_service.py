from typing import List, Optional, Dict

from app.db.file_article_repository import ArticleRepository, FileArticleRepository
from app.model.ingest_request import IngestRequest
from app.services.knowledge_base_service import KnowledgeBaseService


class NaiveGraphIngestService:
    def __init__(self, repo: ArticleRepository):
        self.repo = repo

    def add_article(self, req: IngestRequest) -> Dict:
        meta = self.repo.save_article(req.title, req.text)
        article_id = meta["article_id"]
        title = meta["title"]
        print(meta)

        kb_info = KnowledgeBaseService().update_from_article(
            article_id=article_id,
            title=title,
            text=req.text,
        )

        return {
            **meta,
            "entities_file": kb_info["entities_file"],
            "relations_file": kb_info["relations_file"],
            "kb_is_new": kb_info["is_new"],
            "message": "Article saved and knowledge base updated.",
        }

    def get_article(self, article_id: int) -> Optional[Dict]:
        return self.repo.get_article(article_id)

    def delete_article(self, article_id: int) -> bool:
        return self.repo.delete_article(article_id)

    def list_articles(self) -> List[Dict]:
        return self.repo.list_articles()


graph_ingest_service = NaiveGraphIngestService(FileArticleRepository())
