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
        self.current_model: str = settings.llm_model
        self.prompt_service = PromptService()
        self.graph_service = GraphService(GraphRepository())
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.neo4j_service: Neo4jService | None = None

    def set_model(self, model: str) -> None:
        logger.info("Switching model to: %s", model)
        self.current_model = model

    def update_from_request_async(self, req: AddArticleRequest, is_new: bool) -> None:
        self.executor.submit(self._update_from_article, req.title, req.text, is_new, self.current_model)

    def _update_from_article(self, title: str, text: str, is_new: bool, model: str) -> None:
        try:
            llm = init_chat_model(model)
            if is_new:
                prompt = self.prompt_service.build_prompt("new_graph", title=title, text=text)
            else:
                graph_text = self.graph_service.get_latest_graph_text()
                prompt = self.prompt_service.build_prompt("existing_graph", title=title, text=text, graph=graph_text)

            logger.info("Prompt: %s", prompt)

            if settings.openai_request:
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

            self.graph_service.save_graph(response_to_return)
            self.neo4j_service.push_graph(self.graph_service.get_latest_graph())
        except Exception:
            logger.exception("Failed to update knowledge base from article '%s'", title)

    def build_specific_version(self, graph_id: int) -> None:
        self.neo4j_service.push_graph(self.graph_service.get_graph(graph_id))

    def shutdown(self) -> None:
        self.executor.shutdown(wait=True)

    def clear_knowledge_base(self) -> None:
        logger.info("Clearing knowledge base")
        self.graph_service.save_graph("")
        self.neo4j_service.clean_database()


knowledge_base_service = KnowledgeBaseService()
