import logging

from app.kb.prompts import PROMPTS

logger = logging.getLogger(__name__)


class PromptService:
    def __init__(self, prompt_set: str = "filmweb_pl"):
        self.prompt_set = prompt_set

    def build_prompt(self, prompt_type: str, **kwargs) -> str:
        set_prompts = PROMPTS.get(self.prompt_set, {})
        template = set_prompts.get(prompt_type)

        if template is None:
            template = self._fetch_from_db(f"{self.prompt_set}/{prompt_type}")

        if template is None:
            raise ValueError(
                f"Prompt not found for prompt_set='{self.prompt_set}', "
                f"prompt_type='{prompt_type}'"
            )

        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(
                f"Missing template variable: {e} for prompt_type='{prompt_type}'"
            ) from e

    @staticmethod
    def _fetch_from_db(key: str) -> str | None:
        try:
            from app.config.database import SessionLocal
            from app.kb.model.prompt_entity import PromptEntity
            with SessionLocal() as session:
                entity = session.get(PromptEntity, key)
                return entity.content if entity else None
        except Exception:
            logger.warning("Failed to fetch prompt from DB for key: %s", key)
            return None
