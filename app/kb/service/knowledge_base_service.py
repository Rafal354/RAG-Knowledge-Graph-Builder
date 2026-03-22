import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Tuple

from app.api import api
from app.kb.service.knowledge_extraction_service import knowledge_extraction_service

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self) -> None:
        self.kb_dir = Path(__file__).resolve().parent.parent.parent / "database"
        self.kb_dir.mkdir(parents=True, exist_ok=True)

        self.entities_file = self.kb_dir / "entities.txt"
        self.relations_file = self.kb_dir / "relations.txt"

        self.entities_file.touch(exist_ok=True)
        self.relations_file.touch(exist_ok=True)

        self.executor = ThreadPoolExecutor(max_workers=4)

    def update_from_request_async(self, req) -> None:
        self.executor.submit(self.update_from_article, req.title, req.text)

    def update_from_article(self, title: str, text: str) -> Dict[str, str | bool]:
        is_new = self.entities_file.stat().st_size == 0

        extraction_result = knowledge_extraction_service.extract_knowledge(
            text=text,
            is_new=is_new,
        )

        entities_str, relations_str = self._split_kb_sections(extraction_result)

        self.entities_file.write_text(entities_str, encoding="utf-8")
        self.relations_file.write_text(relations_str, encoding="utf-8")

        api.builder.update_graph()

        return {
            "entities_file": str(self.entities_file),
            "relations_file": str(self.relations_file),
            "is_new": is_new,
        }

    @staticmethod
    def _split_kb_sections(extraction_result: str) -> Tuple[str, str]:
        parts = extraction_result.split("[RELATIONS]", maxsplit=1)

        entities_part = parts[0].replace("[ENTITIES]", "").strip()
        relations_part = parts[1].strip() if len(parts) > 1 else ""

        entities_lines = [
            line.strip()
            for line in entities_part.splitlines()
            if line.strip()
        ]
        relations_lines = [
            line.strip()
            for line in relations_part.splitlines()
            if line.strip()
        ]

        if len(entities_lines) > 1:
            entities_lines = entities_lines[1:]

        return "\n".join(entities_lines), "\n".join(relations_lines)


knowledge_base_service = KnowledgeBaseService()