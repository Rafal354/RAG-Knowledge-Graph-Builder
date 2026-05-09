import textwrap
from typing import Dict


def _clean(text: str) -> str:
    return textwrap.dedent(text).strip()


PROMPTS: Dict[str, Dict[str, str]] = {
    "default_en": {
        "new_graph": _clean("""
            Build a knowledge graph from the article below.

            Extract entities and relations mentioned in the text.

            Return the result exactly in this format:

            [ENTITIES]
            entity_1
            entity_2

            [RELATIONS]
            entity_1 -> relation -> entity_2

            Article title:
            {title}

            Article text:
            {text}
        """),
        "existing_graph": _clean("""
            Update the existing knowledge graph using the new article below.

            The result should represent a merged and consistent knowledge graph based on:
            - the existing graph
            - the new article

            The output should not be based only on the new article.
            It should reflect the combined knowledge from both sources.

            Return the result exactly in this format:

            [ENTITIES]
            entity_1
            entity_2

            [RELATIONS]
            entity_1 -> relation -> entity_2

            Existing knowledge graph:
            {graph}

            Article title:
            {title}

            Article text:
            {text}
        """),
    },
    "default_pl": {
        "new_graph": _clean("""
            Zbuduj graf wiedzy na podstawie poniższego artykułu.

            Wyodrębnij encje i relacje występujące w tekście.
            Encje i relacje zapisz w języku polskim.

            Zwróć wynik dokładnie w następującym formacie:

            [ENTITIES]
            entity_1
            entity_2

            [RELATIONS]
            entity_1 -> relation -> entity_2

            Tytuł artykułu:
            {title}

            Treść artykułu:
            {text}
        """),
        "existing_graph": _clean("""
            Zaktualizuj istniejący graf wiedzy na podstawie nowego artykułu.

            Wynik powinien przedstawiać scalony i spójny graf wiedzy oparty na:
            - istniejącym grafie
            - nowym artykule

            Encje i relacje zapisz w języku polskim.

            Zwróć wynik dokładnie w następującym formacie:

            [ENTITIES]
            entity_1
            entity_2

            [RELATIONS]
            entity_1 -> relation -> entity_2

            Istniejący graf wiedzy:
            {graph}

            Tytuł artykułu:
            {title}

            Treść artykułu:
            {text}
        """),
    },
}
