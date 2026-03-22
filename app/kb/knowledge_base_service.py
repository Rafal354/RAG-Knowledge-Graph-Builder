import logging
import os
from concurrent.futures import ThreadPoolExecutor

from langchain.chat_models import init_chat_model

from app.api import api
from app.graph.graph_repository import GraphRepository
from app.graph.graph_service import GraphService
from app.kb.prompt_service import (
    get_prompt_for_existing_graph,
    get_prompt_for_new_graph,
    get_system_prompt,
)

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self, model_name: str = "gpt-4o-mini") -> None:
        self.graph_service = GraphService(GraphRepository())
        self.llm = init_chat_model(model_name) # needs to be replaceable
        self.executor = ThreadPoolExecutor(max_workers=4)


    def update_from_request_async(self, req, is_new) -> None:
        self.executor.submit(self._update_from_article, req.title, req.text, is_new)

    def _update_from_article(self, title: str, text: str, is_new: bool) -> None:
        system_prompt = get_system_prompt()
        if is_new:
            user_prompt = get_prompt_for_new_graph(title, text)
        else:
            graph_text = self.graph_service.get_latest_graph_text()
            user_prompt = get_prompt_for_existing_graph(title, text, graph_text)

        logger.info(f"User prompt: {user_prompt}")
        logger.info(f"System prompt: {system_prompt}")

        if os.getenv("OPENAI_REQUEST") == "true":
            response = self.llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ])
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
        api.neo4j_service.update_graph()


knowledge_base_service = KnowledgeBaseService()