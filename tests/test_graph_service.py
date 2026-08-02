import unittest

from app.graph.service.graph_service import GraphService
from tests.fakes import FakeGraphRepository, relation_set


class MergeRelationsTests(unittest.TestCase):
    """Testuje GraphService._merge_relations / _normalize_triple w izolacji, bez repozytorium."""

    def test_drops_exact_duplicate_after_normalization(self):
        existing = [("Tim Cook", "jest CEO", "Apple")]
        new = [
            (" tim cook ", "JEST   CEO", "apple"),  # ten sam fakt, inna forma zapisu -> ma zostać odrzucony
            ("Apple", "ma siedzibe w", "Cupertino"),  # nowy, unikalny fakt -> ma zostać dodany
        ]

        merged = GraphService._merge_relations(existing, new)

        self.assertEqual(len(merged), 2)
        self.assertIn(("Tim Cook", "jest CEO", "Apple"), merged)
        self.assertIn(("Apple", "ma siedzibe w", "Cupertino"), merged)

    def test_keeps_relation_differing_in_surface_form(self):
        existing = [("Tim Cook", "jest CEO", "Apple")]
        new = [("Cook", "jest CEO", "Apple")]  # ten sam fakt realnie, ale inny zapis podmiotu

        merged = GraphService._merge_relations(existing, new)

        # mechanizm oparty na normalizacji tekstowej (nie semantycznej) NIE wykrywa
        # tego jako duplikatu - obie trójki mają pozostać w grafie
        self.assertEqual(len(merged), 2)
        self.assertIn(("Tim Cook", "jest CEO", "Apple"), merged)
        self.assertIn(("Cook", "jest CEO", "Apple"), merged)

    def test_merge_is_order_stable_existing_first(self):
        existing = [("A", "r1", "B"), ("B", "r2", "C")]
        new = [("C", "r3", "D")]

        merged = GraphService._merge_relations(existing, new)

        self.assertEqual(merged, [("A", "r1", "B"), ("B", "r2", "C"), ("C", "r3", "D")])


class SaveIncrementalGraphTests(unittest.TestCase):
    """Testuje GraphService.save_incremental_graph end-to-end, na fałszywym repozytorium,
    weryfikując że kolejne 'artykuły' faktycznie budują jeden narastający graf."""

    def setUp(self) -> None:
        self.repo = FakeGraphRepository()
        self.service = GraphService(self.repo)

    def test_first_article_creates_initial_graph(self):
        llm_output = "[RELATIONS]\nTim Cook -> jest CEO -> Apple"

        graph = self.service.save_incremental_graph(llm_output, title="Artykul 1")

        self.assertEqual(graph.version, 1)
        self.assertEqual(relation_set(graph), {("Tim Cook", "jest CEO", "Apple")})

    def test_graph_accumulates_across_multiple_articles(self):
        self.service.save_incremental_graph(
            "[RELATIONS]\nTim Cook -> jest CEO -> Apple",
            title="Artykul 1 - zapowiedz sukcesji",
        )

        # artykul 2 powtarza znany fakt (inna forma zapisu) i dodaje jeden nowy
        g2 = self.service.save_incremental_graph(
            "[RELATIONS]\nTim Cook -> jest CEO -> Apple\nTim Cook -> oglasza -> odejscie",
            title="Artykul 2 - Cook na wylocie",
        )
        self.assertEqual(len(g2.relations), 2, "duplikat z artykulu 1 powinien zostac odrzucony")

        # artykul 3 wprowadza zupelnie nowy watek (inna firma, inna osoba)
        g3 = self.service.save_incremental_graph(
            "[RELATIONS]\nSundar Pichai -> jest CEO -> Google",
            title="Artykul 3 - nastepca ogloszony",
        )

        self.assertEqual(g3.version, 3)
        self.assertEqual(len(g3.relations), 3)
        self.assertEqual(
            relation_set(g3),
            {
                ("Tim Cook", "jest CEO", "Apple"),
                ("Tim Cook", "oglasza", "odejscie"),
                ("Sundar Pichai", "jest CEO", "Google"),
            },
        )

        # graf faktycznie narasta wersja po wersji, a nie jest nadpisywany od zera
        self.assertEqual(self.repo.get_latest_graph().version, 3)
        self.assertEqual(len(self.repo.graphs), 3)
        self.assertEqual(len(self.repo.graphs[0].relations), 1)
        self.assertEqual(len(self.repo.graphs[1].relations), 2)
        self.assertEqual(len(self.repo.graphs[2].relations), 3)

    def test_empty_existing_graph_is_handled(self):
        # brak wczesniejszego grafu (nowa baza wiedzy) - nie powinno wywalic wyjatku
        graph = self.service.save_incremental_graph(
            "[RELATIONS]\nA -> r -> B", title="Pierwszy artykul"
        )
        self.assertEqual(relation_set(graph), {("A", "r", "B")})


if __name__ == "__main__":
    unittest.main()
