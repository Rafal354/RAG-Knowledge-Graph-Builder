import logging
import re

from app.config.database import SessionLocal
from app.kb.model.prompt_config_entity import PromptConfigEntity
from app.kb.model.prompt_entity import PromptEntity

logger = logging.getLogger(__name__)

BUILTIN_CONFIGS: dict[str, dict] = {
    "filmweb_pl": {
        "name": "Filmweb PL",
        "language": "pl",
        "entity_types": (
            "- osoby (aktorzy, reżyserzy, scenarzyści, producenci, autorzy)\n"
            "- dzieła (seriale, filmy, książki, sztuki teatralne)\n"
            "- organizacje (firmy, studia, platformy streamingowe, instytucje)\n"
            "- miejsca (miasta, kraje, lokalizacje geograficzne)\n"
            "- daty i wydarzenia"
        ),
        "rules": (
            "- Encje i relacje zapisuj po polsku\n"
            "- Nie duplikuj relacji w odwrotnej kolejności\n"
            "- Pomijaj postacie fikcyjne i relacje między nimi — interesują nas wyłącznie prawdziwi ludzie i ich związki z dziełami, organizacjami i miejscami\n"
            "- Dozwolone relacje osoby do dzieła: gra rolę w, reżyseruje, produkuje, pisze scenariusz do, komponuje muzykę do, jest autorem\n"
            "- Nie wyciągaj relacji wynikających z fabuły lub opisów postaci fikcyjnych"
        ),
        "examples_positive": (
            "Jakub Kowalski -> gra rolę w -> Serial XYZ\n"
            "Serial XYZ -> jest produkowany przez -> Studio ABC\n"
            "Serial XYZ -> ma premierę -> 22 maja 2025\n"
            "Anna Nowak -> reżyseruje -> Serial XYZ"
        ),
        "examples_negative": (
            "Postać A -> jest mordercą -> Postać B  (relacja fikcyjna)\n"
            "Postać A -> szuka -> Postać B  (relacja fikcyjna)"
        ),
    },
    "typed_pl": {
        "name": "Typed PL",
        "language": "pl",
        "entity_types": (
            "- osoby\n"
            "- organizacje administracyjne, instytucje, NGO, firmy\n"
            "- miasta\n"
            "- kraje\n"
            "- lokalizacje geograficzne inne niż kraj\n"
            "- wydarzenia\n"
            "- daty\n"
            "- adresy mejlowe"
        ),
        "rules": (
            "- Encje i relacje zapisuj po polsku\n"
            "- Nie duplikuj relacji w odwrotnej kolejności"
        ),
        "examples_positive": None,
        "examples_negative": None,
    },
    "typed_2_pl": {
        "name": "Typed 2 PL",
        "language": "pl",
        "entity_types": (
            "- osoby (aktorzy, reżyserzy, autorzy, postacie fikcyjne)\n"
            "- organizacje (firmy, instytucje, platformy streamingowe, studia)\n"
            "- dzieła (seriale, filmy, książki, sztuki teatralne)\n"
            "- miasta i kraje\n"
            "- lokalizacje geograficzne inne niż kraj\n"
            "- wydarzenia\n"
            "- daty\n"
            "- adresy mejlowe"
        ),
        "rules": (
            "- Encje i relacje zapisuj po polsku\n"
            "- Nie duplikuj relacji w odwrotnej kolejności\n"
            "- Wyodrębniaj tylko encje i relacje wprost lub pośrednio wynikające z tekstu"
        ),
        "examples_positive": None,
        "examples_negative": None,
    },
    "typed_en": {
        "name": "Typed EN",
        "language": "en",
        "entity_types": (
            "- people\n"
            "- administrative organizations, institutions, NGOs, companies\n"
            "- cities\n"
            "- countries\n"
            "- geographic locations other than countries\n"
            "- events\n"
            "- dates\n"
            "- e-mail addresses"
        ),
        "rules": (
            "- Write entities and relations in English\n"
            "- Do not duplicate relations in reverse order"
        ),
        "examples_positive": None,
        "examples_negative": None,
    },
    "default_pl": {
        "name": "Default PL",
        "language": "pl",
        "entity_types": "wszystkie typy encji i relacji",
        "rules": "- Encje i relacje zapisuj w języku polskim",
        "examples_positive": None,
        "examples_negative": None,
    },
    "default_en": {
        "name": "Default EN",
        "language": "en",
        "entity_types": "all entity and relation types",
        "rules": "- Write entities and relations in English",
        "examples_positive": None,
        "examples_negative": None,
    },
}


def build_prompt_content(
    entity_types: str,
    rules: str,
    language: str,
    prompt_type: str,
    examples_positive: str | None = None,
    examples_negative: str | None = None,
    mode: str = "structured",
    custom_content: str | None = None,
) -> str:
    if mode == "custom":
        if not custom_content:
            raise ValueError("custom_content is required for custom mode")
        if language == "en":
            suffix: list[str] = []
            if prompt_type == "existing_graph":
                suffix += ["", "Existing knowledge graph:", "{graph}"]
            suffix += ["", "Article title:", "{title}", "", "Article text:", "{text}"]
        else:
            suffix = []
            if prompt_type == "existing_graph":
                suffix += ["", "Istniejący graf wiedzy:", "{graph}"]
            suffix += ["", "Tytuł artykułu:", "{title}", "", "Treść artykułu:", "{text}"]
        return custom_content + "\n" + "\n".join(suffix)

    if language == "en":
        if prompt_type == "new_graph":
            parts = [
                "Build a knowledge graph from the article below.",
                "",
                "Extract only relations between the following entity types:",
                entity_types,
                "",
                "Rules:",
                rules,
                "",
                "Return the result exactly in this format:",
                "",
                "[RELATIONS]",
                "entity_1 -> relation -> entity_2",
            ]
            if examples_positive:
                parts += ["", "Example of correct relations:", examples_positive]
            if examples_negative:
                parts += ["", "Example of relations NOT to extract:", examples_negative]
            parts += ["", "Article title:", "{title}", "", "Article text:", "{text}"]
        else:
            parts = [
                "Update the existing knowledge graph using the new article below.",
                "",
                "Extract only relations between the following entity types:",
                entity_types,
                "",
                "Rules:",
                rules,
                "- Preserve existing relations and add new ones",
                "- If an entity already exists in the graph, use the same name",
                "",
                "Return the result exactly in this format:",
                "",
                "[RELATIONS]",
                "entity_1 -> relation -> entity_2",
            ]
            if examples_positive:
                parts += ["", "Example of correct relations:", examples_positive]
            if examples_negative:
                parts += ["", "Example of relations NOT to extract:", examples_negative]
            parts += [
                "", "Existing knowledge graph:", "{graph}",
                "", "Article title:", "{title}",
                "", "Article text:", "{text}",
            ]
    else:
        if prompt_type == "new_graph":
            parts = [
                "Zbuduj graf wiedzy na podstawie poniższego artykułu.",
                "",
                "Wyodrębniaj wyłącznie relacje między następującymi typami encji:",
                entity_types,
                "",
                "Zasady:",
                rules,
                "",
                "Zwróć wynik dokładnie w następującym formacie:",
                "",
                "[RELACJE]",
                "encja_1 -> relacja -> encja_2",
            ]
            if examples_positive:
                parts += ["", "Przykład poprawnych relacji:", examples_positive]
            if examples_negative:
                parts += ["", "Przykład relacji których NIE wyodrębniamy:", examples_negative]
            parts += ["", "Tytuł artykułu:", "{title}", "", "Treść artykułu:", "{text}"]
        else:
            parts = [
                "Zaktualizuj istniejący graf wiedzy na podstawie nowego artykułu.",
                "",
                "Wyodrębniaj wyłącznie relacje między następującymi typami encji:",
                entity_types,
                "",
                "Zasady:",
                rules,
                "- Zachowaj relacje z istniejącego grafu i dodaj nowe",
                "- Jeśli encja już istnieje w grafie, użyj tej samej nazwy",
                "",
                "Zwróć wynik dokładnie w następującym formacie:",
                "",
                "[RELACJE]",
                "encja_1 -> relacja -> encja_2",
            ]
            if examples_positive:
                parts += ["", "Przykład poprawnych relacji:", examples_positive]
            if examples_negative:
                parts += ["", "Przykład relacji których NIE wyodrębniamy:", examples_negative]
            parts += [
                "", "Istniejący graf wiedzy:", "{graph}",
                "", "Tytuł artykułu:", "{title}",
                "", "Treść artykułu:", "{text}",
            ]
    return "\n".join(parts)


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower().strip())
    return slug.strip("_") or "prompt"


class PromptConfigService:

    def seed_builtins(self) -> None:
        with SessionLocal() as session:
            for key, data in BUILTIN_CONFIGS.items():
                existing = session.get(PromptConfigEntity, key)
                ep = data.get("examples_positive")
                en = data.get("examples_negative")
                if existing is None:
                    session.add(PromptConfigEntity(
                        key=key,
                        name=data["name"],
                        entity_types=data["entity_types"],
                        rules=data["rules"],
                        language=data["language"],
                        is_builtin=True,
                        examples_positive=ep,
                        examples_negative=en,
                        mode="structured",
                        custom_content=None,
                    ))
                else:
                    existing.name = data["name"]
                    existing.entity_types = data["entity_types"]
                    existing.rules = data["rules"]
                    existing.language = data["language"]
                    existing.is_builtin = True
                    existing.examples_positive = ep
                    existing.examples_negative = en
                    existing.mode = "structured"
                    existing.custom_content = None

                for prompt_type in ("new_graph", "existing_graph"):
                    full_key = f"{key}/{prompt_type}"
                    content = build_prompt_content(
                        data["entity_types"], data["rules"], data["language"], prompt_type,
                        examples_positive=ep, examples_negative=en,
                        mode="structured",
                    )
                    existing_prompt = session.get(PromptEntity, full_key)
                    if existing_prompt is None:
                        session.add(PromptEntity(key=full_key, content=content))
                    else:
                        existing_prompt.content = content

            session.commit()
        logger.info("Prompt configs seeded")

    def list_configs(self) -> list[dict]:
        with SessionLocal() as session:
            configs = session.query(PromptConfigEntity).order_by(
                PromptConfigEntity.is_builtin.desc(),
                PromptConfigEntity.name,
            ).all()
            return [
                {
                    "key": c.key,
                    "name": c.name,
                    "entity_types": c.entity_types,
                    "rules": c.rules,
                    "language": c.language,
                    "is_builtin": c.is_builtin,
                    "examples_positive": c.examples_positive,
                    "examples_negative": c.examples_negative,
                    "mode": c.mode,
                    "custom_content": c.custom_content,
                }
                for c in configs
            ]

    def get_config(self, key: str) -> dict | None:
        with SessionLocal() as session:
            c = session.get(PromptConfigEntity, key)
            if c is None:
                return None
            return {
                "key": c.key,
                "name": c.name,
                "entity_types": c.entity_types,
                "rules": c.rules,
                "language": c.language,
                "is_builtin": c.is_builtin,
                "examples_positive": c.examples_positive,
                "examples_negative": c.examples_negative,
                "mode": c.mode,
                "custom_content": c.custom_content,
            }

    def create_config(
        self,
        name: str,
        entity_types: str,
        rules: str,
        language: str,
        examples_positive: str | None = None,
        examples_negative: str | None = None,
        mode: str = "structured",
        custom_content: str | None = None,
    ) -> dict:
        if mode == "custom" and not custom_content:
            raise ValueError("custom_content is required for custom mode")
        base_key = _slugify(name)
        with SessionLocal() as session:
            key = base_key
            suffix = 2
            while session.get(PromptConfigEntity, key) is not None:
                key = f"{base_key}_{suffix}"
                suffix += 1

            config = PromptConfigEntity(
                key=key,
                name=name,
                entity_types=entity_types,
                rules=rules,
                language=language,
                is_builtin=False,
                examples_positive=examples_positive or None,
                examples_negative=examples_negative or None,
                mode=mode,
                custom_content=custom_content or None,
            )
            session.add(config)

            for prompt_type in ("new_graph", "existing_graph"):
                full_key = f"{key}/{prompt_type}"
                content = build_prompt_content(
                    entity_types, rules, language, prompt_type,
                    examples_positive=examples_positive or None,
                    examples_negative=examples_negative or None,
                    mode=mode,
                    custom_content=custom_content or None,
                )
                existing_prompt = session.get(PromptEntity, full_key)
                if existing_prompt is None:
                    session.add(PromptEntity(key=full_key, content=content))
                else:
                    existing_prompt.content = content

            session.commit()
            logger.info("Created prompt config: %s", key)
            return {
                "key": key, "name": name, "entity_types": entity_types, "rules": rules,
                "language": language, "is_builtin": False,
                "examples_positive": examples_positive or None,
                "examples_negative": examples_negative or None,
                "mode": mode,
                "custom_content": custom_content or None,
            }

    def update_config(
        self,
        key: str,
        name: str,
        entity_types: str,
        rules: str,
        language: str,
        examples_positive: str | None = None,
        examples_negative: str | None = None,
        mode: str = "structured",
        custom_content: str | None = None,
    ) -> dict | None:
        with SessionLocal() as session:
            config = session.get(PromptConfigEntity, key)
            if config is None:
                return None
            config.name = name
            config.entity_types = entity_types
            config.rules = rules
            config.language = language
            config.examples_positive = examples_positive or None
            config.examples_negative = examples_negative or None
            config.mode = mode
            config.custom_content = custom_content or None

            for prompt_type in ("new_graph", "existing_graph"):
                full_key = f"{key}/{prompt_type}"
                content = build_prompt_content(
                    entity_types, rules, language, prompt_type,
                    examples_positive=examples_positive or None,
                    examples_negative=examples_negative or None,
                    mode=mode,
                    custom_content=custom_content or None,
                )
                existing_prompt = session.get(PromptEntity, full_key)
                if existing_prompt is None:
                    session.add(PromptEntity(key=full_key, content=content))
                else:
                    existing_prompt.content = content

            session.commit()
            logger.info("Updated prompt config: %s", key)
            return {
                "key": key, "name": name, "entity_types": entity_types, "rules": rules,
                "language": language, "is_builtin": config.is_builtin,
                "examples_positive": examples_positive or None,
                "examples_negative": examples_negative or None,
                "mode": mode,
                "custom_content": custom_content or None,
            }

    def delete_config(self, key: str) -> bool:
        with SessionLocal() as session:
            config = session.get(PromptConfigEntity, key)
            if config is None:
                return False
            if config.is_builtin:
                return False
            session.delete(config)
            for prompt_type in ("new_graph", "existing_graph"):
                full_key = f"{key}/{prompt_type}"
                prompt = session.get(PromptEntity, full_key)
                if prompt is not None:
                    session.delete(prompt)
            session.commit()
            return True

    def get_prompt_content(self, key: str) -> str | None:
        with SessionLocal() as session:
            entity = session.get(PromptEntity, key)
            return entity.content if entity else None


prompt_config_service = PromptConfigService()
