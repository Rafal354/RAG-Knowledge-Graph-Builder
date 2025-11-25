from pathlib import Path
from typing import Dict

from app.services.knowledge_extraction_service import knowledge_extraction_service


class KnowledgeBaseService:
    """
    Service responsible for storing and updating the local KB file
    using GPT-based extraction.
    """

    def __init__(self, kb_dir: Path = None, kb_filename: str = "kb.txt"):
        project_root = Path(__file__).resolve().parents[2]

        self.kb_dir = kb_dir or (project_root / "database")
        self.kb_dir.mkdir(parents=True, exist_ok=True)

        self.kb_file = self.kb_dir / kb_filename
        if not self.kb_file.exists():
            self.kb_file.touch()

    def update_from_article(self, article_id: int, title: str, text: str) -> Dict:
        """
        - ensures KB file exists
        - calls GPT model (via LangChain) for extraction
        - writes the extracted knowledge into kb.txt
        """

        is_new = self.kb_file.stat().st_size == 0

        extraction_result = knowledge_extraction_service.extract_knowledge(
            text=text,
            article_id=article_id,
            title=title,
            is_new=is_new,
            kb_file=self.kb_file
        )

        # with self.kb_file.open("w", encoding="utf-8") as f:
        #     f.write(extraction_result)
        #     f.write("\n\n")

        return {
            "kb_file": str(self.kb_file),
            "is_new": is_new,
        }
