import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

from app.db.article_repository import ArticleRepository

BASE_DIR = Path(__file__).resolve().parent.parent.parent / "database"
INDEX_FILE = BASE_DIR / "index.json"

BASE_DIR.mkdir(parents=True, exist_ok=True)
if not INDEX_FILE.exists():
    INDEX_FILE.write_text("[]", encoding="utf-8")


def _generate_next_id(index: List[Dict]) -> int:
    if not index:
        return 1
    existing_ids = [int(item["article_id"]) for item in index]
    return max(existing_ids) + 1


class FileArticleRepository(ArticleRepository):

    def __init__(self, base_dir: Path = BASE_DIR, index_file: Path = INDEX_FILE):
        self.base_dir = base_dir
        self.index_file = index_file

    def _read_index(self) -> List[Dict]:
        raw = self.index_file.read_text(encoding="utf-8")
        try:
            return json.loads(raw)
        except:
            return []

    def _write_index(self, items: List[Dict]):
        self.index_file.write_text(
            json.dumps(items, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def save_article(self, title: str, text: str) -> Dict:
        index = self._read_index()

        print("INDEX:", index)

        new_id = _generate_next_id(index)
        print("NEW ID:", new_id)
        filename = self.base_dir / "articles" / f"{new_id}.txt"
        print("FILENAME:", filename)
        try:
            filename.write_text(text, encoding="utf-8")
        except Exception as e:
            print(e)

        meta = {
            "article_id": new_id,
            "title": title,
            "filename": str(filename),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "text_length": len(text)
        }

        index.append(meta)
        self._write_index(index)

        return meta

    def get_article(self, article_id: int) -> Optional[Dict]:
        index = self._read_index()
        meta = next((m for m in index if int(m["article_id"]) == article_id), None)
        if not meta:
            return None

        file_path = Path(meta["filename"])
        if not file_path.exists():
            return None

        text = file_path.read_text(encoding="utf-8")
        return {**meta, "text": text}

    def delete_article(self, article_id: int) -> bool:
        index = self._read_index()
        new_index = [m for m in index if int(m["article_id"]) != article_id]

        if len(new_index) == len(index):
            return False

        self._write_index(new_index)

        file_path = self.base_dir / f"{article_id}.txt"
        if file_path.exists():
            file_path.unlink()

        return True

    def list_articles(self) -> List[Dict]:
        return self._read_index()
