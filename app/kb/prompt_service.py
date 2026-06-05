from app.kb.prompts import PROMPTS


class PromptService:
    def __init__(self, prompt_set: str = "filmweb_pl"):
        self.prompt_set = prompt_set

    def build_prompt(self, prompt_type: str, **kwargs) -> str:
        try:
            template = PROMPTS[self.prompt_set][prompt_type]
        except KeyError as e:
            raise ValueError(
                f"Prompt not found for prompt_set='{self.prompt_set}', "
                f"prompt_type='{prompt_type}'"
            ) from e

        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(
                f"Missing template variable: {e} for prompt_type='{prompt_type}'"
            ) from e
