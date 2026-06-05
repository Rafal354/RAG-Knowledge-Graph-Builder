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
            entity_1 -> relacja -> entity_2

            Istniejący graf wiedzy:
            {graph}

            Tytuł artykułu:
            {title}

            Treść artykułu:
            {text}
        """),
    },
    "typed_pl": {
        "new_graph": _clean("""
            Zbuduj graf wiedzy na podstawie poniższego artykułu.

            Wyodrębniaj wyłącznie relacje między następującymi typami encji:
            - osoby
            - organizacje administracyjne, instytucje, NGO, firmy
            - miasta
            - kraje
            - lokalizacje geograficzne inne niż kraj
            - wydarzenia
            - daty
            - adresy mejlowe

            Zasady:
            - Encje i relacje zapisuj po polsku
            - Nie duplikuj relacji w odwrotnej kolejności

            Zwróć wynik dokładnie w następującym formacie:

            [RELACJE]
            encja_1 -> relacja -> encja_2

            Przykład:
            Łukasz Kowalski -> jest reżyserem -> Film XYZ
            Film XYZ -> jest produkowany przez -> Studio ABC

            Tytuł artykułu:
            {title}

            Treść artykułu:
            {text}
        """),
        "existing_graph": _clean("""
            Zaktualizuj istniejący graf wiedzy na podstawie nowego artykułu.

            Wyodrębniaj wyłącznie relacje między następującymi typami encji:
            - osoby
            - organizacje administracyjne, instytucje, NGO, firmy
            - miasta
            - kraje
            - lokalizacje geograficzne inne niż kraj
            - wydarzenia
            - daty
            - adresy mejlowe

            Zasady:
            - Encje i relacje zapisuj po polsku
            - Nie duplikuj relacji w odwrotnej kolejności
            - Zachowaj relacje z istniejącego grafu i dodaj nowe
            - Jeśli encja już istnieje w grafie, użyj tej samej nazwy

            Zwróć wynik dokładnie w następującym formacie:

            [RELACJE]
            encja_1 -> relacja -> encja_2

            Istniejący graf wiedzy:
            {graph}

            Tytuł artykułu:
            {title}

            Treść artykułu:
            {text}
        """),
    },
    "typed_en": {
        "new_graph": _clean("""
            Build a knowledge graph from the article below.

            Extract only relations between the following entity types:
            - people
            - administrative organizations, institutions, NGOs, companies
            - cities
            - countries
            - geographic locations other than countries
            - events
            - dates
            - e-mail addresses

            Rules:
            - Write entities and relations in English
            - Do not duplicate relations in reverse order

            Return the result exactly in this format:

            [RELATIONS]
            entity_1 -> relation -> entity_2

            Example:
            John Smith -> is director of -> Film XYZ
            Film XYZ -> is produced by -> Studio ABC

            Article title:
            {title}

            Article text:
            {text}
        """),
        "existing_graph": _clean("""
            Update the existing knowledge graph using the new article below.

            Extract only relations between the following entity types:
            - people
            - administrative organizations, institutions, NGOs, companies
            - cities
            - countries
            - geographic locations other than countries
            - events
            - dates
            - e-mail addresses

            Rules:
            - Write entities and relations in English
            - Do not duplicate relations in reverse order
            - Preserve existing relations and add new ones
            - If an entity already exists in the graph, use the same name

            Return the result exactly in this format:

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
    "filmweb_pl": {
        "new_graph": _clean("""
            Zbuduj graf wiedzy na podstawie poniższego artykułu.

            Wyodrębniaj wyłącznie relacje między następującymi typami encji ze świata rzeczywistego:
            - osoby (aktorzy, reżyserzy, scenarzyści, producenci, autorzy)
            - dzieła (seriale, filmy, książki, sztuki teatralne)
            - organizacje (firmy, studia, platformy streamingowe, instytucje)
            - miejsca (miasta, kraje, lokalizacje geograficzne)
            - daty i wydarzenia

            Zasady:
            - Encje i relacje zapisuj po polsku
            - Nie duplikuj relacji w odwrotnej kolejności
            - Pomijaj postacie fikcyjne i relacje między nimi — interesują nas wyłącznie prawdziwi ludzie i ich związki z dziełami, organizacjami i miejscami
            - Dozwolone relacje osoby do dzieła: gra rolę w, reżyseruje, produkuje, pisze scenariusz do, komponuje muzykę do, jest autorem
            - Nie wyciągaj relacji wynikających z fabuły lub opisów postaci fikcyjnych

            Zwróć wynik dokładnie w następującym formacie:

            [RELACJE]
            encja_1 -> relacja -> encja_2

            Przykład poprawnych relacji:
            Jakub Kowalski -> gra rolę w -> Serial XYZ
            Serial XYZ -> jest produkowany przez -> Studio ABC
            Serial XYZ -> ma premierę -> 22 maja 2025
            Anna Nowak -> reżyseruje -> Serial XYZ

            Przykład relacji których NIE wyodrębniamy:
            Postać A -> jest mordercą -> Postać B  (relacja fikcyjna)
            Postać A -> szuka -> Postać B  (relacja fikcyjna)

            Tytuł artykułu:
            {title}

            Treść artykułu:
            {text}
        """),
        "existing_graph": _clean("""
            Zaktualizuj istniejący graf wiedzy na podstawie nowego artykułu.

            Wyodrębniaj wyłącznie relacje między następującymi typami encji ze świata rzeczywistego:
            - osoby (aktorzy, reżyserzy, scenarzyści, producenci, autorzy)
            - dzieła (seriale, filmy, książki, sztuki teatralne)
            - organizacje (firmy, studia, platformy streamingowe, instytucje)
            - miejsca (miasta, kraje, lokalizacje geograficzne)
            - daty i wydarzenia

            Zasady:
            - Encje i relacje zapisuj po polsku
            - Nie duplikuj relacji w odwrotnej kolejności
            - Pomijaj postacie fikcyjne i relacje między nimi — interesują nas wyłącznie prawdziwi ludzie i ich związki z dziełami, organizacjami i miejscami
            - Dozwolone relacje osoby do dzieła: gra rolę w, reżyseruje, produkuje, pisze scenariusz do, komponuje muzykę do, jest autorem
            - Nie wyciągaj relacji wynikających z fabuły lub opisów postaci fikcyjnych
            - Zachowaj relacje z istniejącego grafu i dodaj nowe
            - Jeśli encja już istnieje w grafie, użyj tej samej nazwy

            Zwróć wynik dokładnie w następującym formacie:

            [RELACJE]
            encja_1 -> relacja -> encja_2

            Przykład poprawnych relacji:
            Jakub Kowalski -> gra rolę w -> Serial XYZ
            Serial XYZ -> jest produkowany przez -> Studio ABC
            Serial XYZ -> ma premierę -> 22 maja 2025
            Anna Nowak -> reżyseruje -> Serial XYZ

            Przykład relacji których NIE wyodrębniamy:
            Postać A -> jest mordercą -> Postać B  (relacja fikcyjna)
            Postać A -> szuka -> Postać B  (relacja fikcyjna)

            Istniejący graf wiedzy:
            {graph}

            Tytuł artykułu:
            {title}

            Treść artykułu:
            {text}
        """),
    },
    "typed_2_pl": {
        "new_graph": _clean("""
            Zbuduj graf wiedzy na podstawie poniższego artykułu.

            Wyodrębniaj wyłącznie relacje między następującymi typami encji:
            - osoby (aktorzy, reżyserzy, autorzy, postacie fikcyjne)
            - organizacje (firmy, instytucje, platformy streamingowe, studia)
            - dzieła (seriale, filmy, książki, sztuki teatralne)
            - miasta i kraje
            - lokalizacje geograficzne inne niż kraj
            - wydarzenia
            - daty
            - adresy mejlowe

            Zasady:
            - Encje i relacje zapisuj po polsku
            - Nie duplikuj relacji w odwrotnej kolejności
            - Wyodrębniaj tylko encje i relacje wprost lub pośrednio wynikające z tekstu

            Zwróć wynik dokładnie w następującym formacie:

            [RELACJE]
            encja_1 -> relacja -> encja_2

            Przykład:
            Jakub Kowalski -> jest reżyserem -> Serial XYZ
            Serial XYZ -> jest produkowany przez -> Studio ABC
            Serial XYZ -> ma premierę -> 22 maja 2025
            Studio ABC -> jest dostępne w -> Polsce

            Tytuł artykułu:
            {title}

            Treść artykułu:
            {text}
        """),
        "existing_graph": _clean("""
            Zaktualizuj istniejący graf wiedzy na podstawie nowego artykułu.

            Wyodrębniaj wyłącznie relacje między następującymi typami encji:
            - osoby
            - organizacje administracyjne, instytucje, NGO, firmy
            - miasta
            - kraje
            - lokalizacje geograficzne inne niż kraj
            - wydarzenia
            - daty
            - adresy mejlowe

            Zasady:
            - Encje i relacje zapisuj po polsku
            - Nie duplikuj relacji w odwrotnej kolejności
            - Zachowaj relacje z istniejącego grafu i dodaj nowe
            - Jeśli encja już istnieje w grafie, użyj tej samej nazwy

            Zwróć wynik dokładnie w następującym formacie:

            [RELACJE]
            encja_1 -> relacja -> encja_2

            Istniejący graf wiedzy:
            {graph}

            Tytuł artykułu:
            {title}

            Treść artykułu:
            {text}
        """),
    },
}
