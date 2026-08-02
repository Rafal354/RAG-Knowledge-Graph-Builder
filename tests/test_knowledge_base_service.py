import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.graph.service.graph_service import GraphService
from app.kb.knowledge_base_service import KnowledgeBaseService
from tests.fakes import FakeGraphRepository, relation_set


def fake_llm_response(content: str) -> SimpleNamespace:
    """Kształt obiektu zwracanego przez langchain llm.invoke(...) - potrzebujemy tylko .content."""
    return SimpleNamespace(content=content)


class KnowledgeBaseServiceIncrementalGraphTests(unittest.TestCase):
    """Test praktycznie end-to-end: prawdziwy KnowledgeBaseService._update_from_article,
    ale z zamockowanym wywołaniem LLM (langchain init_chat_model) i zamockowanym repozytorium
    grafu (bez prawdziwej bazy danych) - sprawdza, ze kolejne artykuly realnie buduja
    narastajacy, scalany graf, tak jak w produkcyjnej sciezce kodu."""

    def setUp(self) -> None:
        self.service = KnowledgeBaseService()
        # podmieniamy prawdziwe repozytorium (SQLAlchemy + realna baza) na fake w pamieci
        self.repo = FakeGraphRepository()
        self.service.graph_service = GraphService(self.repo)
        self.service.current_model = "gemma-4-26b-a4b-it"  # trafia w gałąź `else: init_chat_model(...)`

    def _run_article(self, title: str, text: str) -> None:
        # wywolanie bezposrednie (synchroniczne), zamiast update_from_request_async,
        # zeby test byl deterministyczny i nie zalezal od ThreadPoolExecutor
        self.service._update_from_article(title=title, text=text, model=self.service.current_model)

    @patch("app.kb.knowledge_base_service.settings")
    @patch("app.kb.knowledge_base_service.init_chat_model")
    def test_sequential_articles_build_one_incremental_graph(self, mock_init_chat_model, mock_settings):
        mock_settings.openai_request = True
        mock_llm = mock_init_chat_model.return_value
        mock_llm.invoke.side_effect = [
            fake_llm_response("[RELATIONS]\nTim Cook -> jest CEO -> Apple"),
            fake_llm_response(
                "[RELATIONS]\n"
                "Tim Cook -> jest CEO -> Apple\n"  # duplikat z artykulu 1 (inna forma zapisu niżej)
                "Tim Cook -> oglasza -> odejscie"
            ),
            fake_llm_response("[RELATIONS]\nSundar Pichai -> jest CEO -> Google"),
        ]

        self._run_article("Artykul 1 - zapowiedz sukcesji", "tresc artykulu 1...")
        self._run_article("Artykul 2 - Cook na wylocie", "tresc artykulu 2...")
        self._run_article("Artykul 3 - nastepca ogloszony", "tresc artykulu 3...")

        self.assertIsNone(self.service.last_error)
        self.assertEqual(mock_init_chat_model.call_count, 3)

        latest = self.repo.get_latest_graph()
        self.assertEqual(latest.version, 3)
        self.assertEqual(
            relation_set(latest),
            {
                ("Tim Cook", "jest CEO", "Apple"),
                ("Tim Cook", "oglasza", "odejscie"),
                ("Sundar Pichai", "jest CEO", "Google"),
            },
        )

        # graf faktycznie narasta wersja po wersji, nie jest nadpisywany od zera
        self.assertEqual([len(g.relations) for g in self.repo.graphs], [1, 2, 3])

        # zawsze prompt "new_graph" - nawet gdy istniejacy graf nie jest juz pusty
        self.assertTrue(all(g.prompt_key.endswith("/new_graph") for g in self.repo.graphs))

    @patch("app.kb.knowledge_base_service.settings")
    @patch("app.kb.knowledge_base_service.init_chat_model")
    def test_llm_receives_isolated_article_without_existing_graph_in_prompt(self, mock_init_chat_model, mock_settings):
        mock_settings.openai_request = True
        mock_llm = mock_init_chat_model.return_value
        mock_llm.invoke.side_effect = [
            fake_llm_response("[RELATIONS]\nA -> r -> B"),
            fake_llm_response("[RELATIONS]\nC -> r2 -> D"),
        ]

        self._run_article("Pierwszy", "tresc 1")
        self._run_article("Drugi", "tresc 2")

        # przy drugim wywolaniu graf nie jest juz pusty, ale prompt do modelu
        # i tak nie powinien zawierac zadnych sladow istniejacego grafu
        second_call_prompt = mock_llm.invoke.call_args_list[1].args[0]
        self.assertNotIn("Istniejący graf wiedzy", second_call_prompt)
        self.assertIn("Drugi", second_call_prompt)


if __name__ == "__main__":
    unittest.main()
