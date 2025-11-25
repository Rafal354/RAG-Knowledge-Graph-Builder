from pathlib import Path
from textwrap import dedent
from typing import Optional

from langchain.chat_models import init_chat_model


class KnowledgeExtractionService:
    """
    Service responsible for:
    - building the extraction prompt
    - calling the LLM
    - returning extracted knowledge text
    """

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = init_chat_model(model_name)

    def _build_extraction_prompt(
        self,
        text: str,
        article_id: int,
        title: str,
        is_new: bool,
        kb_text: str = "",
    ) -> str:
        if is_new:
            mode_instruction = (
                "Nie ma jeszcze bazy wiedzy. Na podstawie tekstu wygeneruj pierwszą bazę wiedzy."
            )
            kb_section = ""
        else:
            mode_instruction = (
                "Istnieje już baza wiedzy. Na podstawie nowego tekstu dodaj TYLKO podmioty i relacje, "
                "które jeszcze nie istnieją."
            )
            kb_section = f"""
            Oto aktualna baza wiedzy:
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

    def extract_knowledge(
        self,
        *,
        text: str,
        article_id: int,
        title: str,
        is_new: bool,
        kb_file: Optional[Path] = None,
        kb_text: Optional[str] = None,
    ) -> str:
        """
        Extracts knowledge from article text using the LLM.

        You can pass either:
        - kb_text directly, or
        - kb_file (it will be read if not is_new)
        """

        # Determine current KB text (if any)
        if not is_new:
            if kb_text is None and kb_file is not None and kb_file.exists():
                kb_text = kb_file.read_text(encoding="utf-8")
        else:
            kb_text = ""

        prompt = self._build_extraction_prompt(
            text=text,
            article_id=article_id,
            title=title,
            is_new=is_new,
            kb_text=kb_text or "",
        )

        # response = self.llm.invoke([
        #     {"role": "system", "content": "Jesteś systemem do ekstrakcji wiedzy."},
        #     {"role": "user", "content": prompt},
        # ])

        mock = f"""
        [ENTITIES]
        MockEntity1
        MockEntity2

        [RELATIONS]
        MockEntity1 -> mock_relation -> MockEntity2
        """

        # return response.content.strip()
        return mock.strip()


knowledge_extraction_service = KnowledgeExtractionService()
