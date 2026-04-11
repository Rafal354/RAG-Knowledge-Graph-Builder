import logging
from concurrent.futures import ThreadPoolExecutor

from langchain.chat_models import init_chat_model

from app.config.settings import settings
from app.graph.repository.graph_repository import GraphRepository
from app.graph.service.graph_service import GraphService
from app.kb.prompt_service import PromptService
from app.neo4j.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self) -> None:
        self.prompt_service = PromptService()
        self.graph_service = GraphService(GraphRepository())
        self.llm = init_chat_model(settings.llm_model)  # needs to be replaceable
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.neo4j_service: Neo4jService | None = None

    def update_from_request_async(self, req, is_new) -> None:
        self.executor.submit(self._update_from_article, req.title, req.text, is_new)

    def _update_from_article(self, title: str, text: str, is_new: bool) -> None:
        if is_new:
            prompt = self.prompt_service.build_prompt("new_graph", title=title, text=text)
        else:
            graph_text = self.graph_service.get_latest_graph_text()
            prompt = self.prompt_service.build_prompt("existing_graph", title=title, text=text, graph=graph_text)

        logger.info(f"Prompt: {prompt}")

        if settings.openai_request:
            response = self.llm.invoke(prompt)
            logger.info(f"Response (LLM): {response}")
            response_to_return = response.content.strip()
        else:
            mock = f"""
                    [ENTITIES]
                    entity_1
                    entity_2
                    entity_3

                    [RELATIONS]
                    entity_1 -> relation_1 -> entity_2
                    entity_2 -> relation_2 -> entity_3
                    """
            logger.info(f"Response (mock): {mock}")
            response_to_return = mock.strip()

        logger.info(f"Response: {response_to_return}")

        self.graph_service.save_graph(response_to_return)
        self.neo4j_service.update_graph()

    def build_specific_version(self, graph_id: int) -> None:
        self.neo4j_service.build_specific_version(graph_id)

    def shutdown(self) -> None:
        self.executor.shutdown(wait=True)

    def clear_knowledge_base(self) -> None:
        logger.info("Clearing knowledge base")
        self.graph_service.save_graph("")
        self.neo4j_service.clean_database()


knowledge_base_service = KnowledgeBaseService()
