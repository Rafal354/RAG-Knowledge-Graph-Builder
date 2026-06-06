import logging
import os
from concurrent.futures import ThreadPoolExecutor

from langchain.chat_models import init_chat_model

from app.articles.dto.add_article_request import AddArticleRequest
from app.config.settings import settings
from app.graph.repository.graph_repository import GraphRepository
from app.graph.service.graph_service import GraphService
from app.kb.prompt_service import PromptService
from app.neo4j.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self) -> None:
        if settings.anthropic_api_key:
            os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
        if settings.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        if settings.google_api_key:
            os.environ["GOOGLE_API_KEY"] = settings.google_api_key
        if settings.alibaba_api_key:
            os.environ["ALIBABA_API_KEY"] = settings.alibaba_api_key
        if settings.openrouter_api_key:
            os.environ["OPENROUTER_API_KEY"] = settings.openrouter_api_key
        self.current_model: str = settings.llm_model
        self.prompt_service = PromptService()
        self.graph_service = GraphService(GraphRepository())
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.neo4j_service: Neo4jService | None = None
        self.last_error: str | None = None
        self.processing: bool = False

    def set_model(self, model: str) -> None:
        logger.info("Switching model to: %s", model)
        self.current_model = model

    def set_prompt_set(self, key: str) -> None:
        logger.info("Switching prompt set to: %s", key)
        self.prompt_service.prompt_set = key

    def get_status(self) -> dict:
        return {"processing": self.processing, "error": self.last_error}

    def update_from_request_async(self, req: AddArticleRequest, article_id: int | None = None) -> None:
        self.last_error = None
        self.processing = True
        self.executor.submit(self._update_from_article, req.title, req.text, self.current_model, article_id)

    def _update_from_article(self, title: str, text: str, model: str, article_id: int | None = None) -> None:
        try:
            graph_text = self.graph_service.get_latest_graph_text()
            if not graph_text or graph_text.strip() == "[RELATIONS]":
                prompt_type = "new_graph"
                prompt = self.prompt_service.build_prompt(prompt_type, title=title, text=text)
            else:
                prompt_type = "existing_graph"
                prompt = self.prompt_service.build_prompt(prompt_type, title=title, text=text, graph=graph_text)
            prompt_key = f"{self.prompt_service.prompt_set}/{prompt_type}"

            logger.info("Prompt:\n%s", prompt)

            if settings.openai_request:
                if model.startswith("local:"):
                    from openai import OpenAI
                    client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio", timeout=600.0)
                    completion = client.chat.completions.create(
                        model=model[len("local:"):],
                        messages=[{"role": "user", "content": prompt}],
                    )
                    logger.info("Response (LM Studio): %s", completion)
                    response_to_return = completion.choices[0].message.content.strip()
                elif model.startswith("qwen"):
                    from openai import OpenAI
                    client = OpenAI(
                        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
                        api_key=settings.alibaba_api_key,
                        timeout=600.0,
                    )
                    completion = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        extra_body={"enable_thinking": False},
                    )
                    logger.info("Response (Alibaba): %s", completion)
                    response_to_return = completion.choices[0].message.content.strip()
                elif "/" in model:
                    from openai import OpenAI
                    client = OpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=settings.openrouter_api_key,
                        timeout=600.0,
                    )
                    completion = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    logger.info("Response (OpenRouter): %s", completion)
                    response_to_return = completion.choices[0].message.content.strip()
                else:
                    llm = init_chat_model(model, timeout=600)
                    response = llm.invoke(prompt)
                    logger.info("Response (LLM): %s", response)
                    response_to_return = response.content.strip()
            else:
                mock = """
                        [ENTITIES]
                        entity_1
                        entity_2
                        entity_3

                        [RELATIONS]
                        entity_1 -> relation_1 -> entity_2
                        entity_2 -> relation_2 -> entity_3
                        """
                logger.info("Response (mock): %s", mock)
                response_to_return = mock.strip()

            logger.info("Response: %s", response_to_return)

            self.graph_service.save_graph(response_to_return, title=title, model=model, article_id=article_id, prompt_key=prompt_key)
            try:
                self.neo4j_service.push_graph(self.graph_service.get_latest_graph())
            except Exception:
                logger.warning("Neo4j unavailable — skipping graph visualization update")
        except Exception as e:
            self.last_error = str(e)
            logger.exception("Failed to update knowledge base from article '%s'", title)
        finally:
            self.processing = False

    def build_specific_version(self, graph_id: int) -> None:
        self.neo4j_service.push_graph(self.graph_service.get_graph(graph_id))

    def shutdown(self) -> None:
        self.executor.shutdown(wait=True)

    def clear_knowledge_base(self) -> None:
        logger.info("Clearing knowledge base")
        self.graph_service.save_graph("")
        try:
            self.neo4j_service.clean_database()
        except Exception:
            logger.warning("Neo4j unavailable — skipping Neo4j cleanup")


knowledge_base_service = KnowledgeBaseService()
