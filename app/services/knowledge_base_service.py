import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict

from app.api import api
from app.services.knowledge_extraction_service import knowledge_extraction_service

executor = ThreadPoolExecutor(max_workers=4)

def _update_kb_async(title: str, text: str) -> None:
    try:
        time.sleep(10)
        knowledge_base_service.update_from_article(title=title, text=text)
    except Exception as e:
        print(f"Knowledge base update failed: {e}")

def split_kb_sections(extraction_result):

    parts = extraction_result.split("[RELATIONS]")
    entities_part = parts[0].replace("[ENTITIES]", "").strip()
    relations_part = parts[1].strip() if len(parts) > 1 else ""

    entities_lines = [
        line.strip() for line in entities_part.splitlines()
        if line.strip()
    ]

    relations_lines = [
        line.strip() for line in relations_part.splitlines()
        if line.strip()
    ]

    if len(entities_lines) > 1:
        entities_lines = entities_lines[1:]

    entities_str = "\n".join(entities_lines)
    relations_str = "\n".join(relations_lines)

    return entities_str, relations_str


class KnowledgeBaseService:
    def __init__(self):
        self.kb_dir = Path(__file__).resolve().parent.parent.parent / "database"
        self.kb_dir.mkdir(parents=True, exist_ok=True)

        self.entities_file = self.kb_dir / "entities.txt"
        if not self.entities_file.exists():
            self.entities_file.touch()

        self.relations_file = self.kb_dir / "relations.txt"
        if not self.relations_file.exists():
            self.relations_file.touch()

    def update_fun(self, req) -> None:
        executor.submit(_update_kb_async, req.title, req.text)




    def update_from_article(self, title: str, text: str) -> Dict:
        is_new = self.entities_file.stat().st_size == 0

        extraction_result = knowledge_extraction_service.extract_knowledge(text=text, is_new=is_new)

        entities_str, relations_str = split_kb_sections(extraction_result)

        with self.entities_file.open("w", encoding="utf-8") as f:
            f.write(entities_str)
            # f.write("\n\n")

        with self.relations_file.open("w", encoding="utf-8") as f:
            f.write(relations_str)
            # f.write("\n\n")

        api.builder.update_graph()

        return {
            "entities_file": str(self.entities_file),
            "relations_file": str(self.relations_file),
            "is_new": is_new,
        }

knowledge_base_service = KnowledgeBaseService()
