import os
from pathlib import Path
from textwrap import dedent

from langchain.chat_models import init_chat_model

BASE_DIR = Path(__file__).resolve().parent.parent.parent / "database"
entities_file = BASE_DIR / "entities.txt"
relations_file = BASE_DIR / "relations.txt"

def add_knowledge_base():
    with open(entities_file, "r", encoding="utf-8") as f:
        entities_content = f.read().strip()

    with open(relations_file, "r", encoding="utf-8") as f:
        relations_content = f.read().strip()

    return (
        "[ENTITIES]\n"
        f"{entities_content}\n"
        f"\n"
        "[RELATIONS]\n"
        f"{relations_content}"
    )


def _build_extraction_prompt(text: str,is_new: bool) -> str:
    kb_text = add_knowledge_base()

    print("IS NEW?", is_new)

    if is_new:
        mode_instruction = (
            "Nie istnieje jeszcze żadna baza wiedzy. "
            "Na podstawie dostarczonego tekstu wygeneruj pierwszą bazę wiedzy."
        )
        kb_section = ""
    else:
        mode_instruction = (
            "Istnieje już baza wiedzy. "
            "Na podstawie nowego tekstu zaktualizuj bazę wiedzy."
        )
        kb_section = f"""
            Aktualna baza wiedzy:
            \"\"\"
            {kb_text}
            \"\"\"
            """

    return dedent(f"""
        {mode_instruction}

        {kb_section}

        Format odpowiedzi:

        [ENTITIES]
        Podmiot A
        Podmiot B
        ...

        [RELATIONS]
        Podmiot A -> relacja -> Podmiot B
        ...

        Nowy tekst:
        \"\"\"
        {text}
        \"\"\"
        """).strip()


class KnowledgeExtractionService:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = init_chat_model(model_name)

    def extract_knowledge(
            self,
            text: str,
            is_new: bool
    ) -> str:

        prompt = _build_extraction_prompt(
            text=text,
            is_new=is_new
        )

        print("ENV: ", os.getenv("OPENAI_REQUEST"))

        if os.getenv("OPENAI_REQUEST") == "true":
            response = self.llm.invoke([
                {"role": "system", "content": "Jesteś systemem do ekstrakcji wiedzy."},
                {"role": "user", "content": prompt},
            ])

            return response.content.strip()
        else:
            mock = f"""
                    [ENTITIES]
                    MockEntity1
                    MockEntity2

                    [RELATIONS]
                    MockEntity1 -> mock_relation -> MockEntity2
                    """
            return mock.strip()


knowledge_extraction_service = KnowledgeExtractionService()
