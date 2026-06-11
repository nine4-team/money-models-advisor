import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from money_model_architect.retrieval import Chunk, CorpusIndex


class FakeEmbeddingClient:
    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        lowered = text.lower()
        return [
            float("cac" in lowered or "acquisition" in lowered),
            float("payback" in lowered),
            float("upsell" in lowered),
            float("continuity" in lowered or "recurring" in lowered),
        ]


def test_index() -> CorpusIndex:
    return CorpusIndex(
        [
            Chunk(
                id="payback-period:0",
                chapter="payback-period",
                layer="unit-economics",
                layers=("unit-economics",),
                text="CAC and payback period determine whether acquisition is recovered.",
                char_start=0,
                char_end=72,
            ),
            Chunk(
                id="upsells:0",
                chapter="upsells",
                layer="upsells",
                layers=("upsells",),
                text="An upsell happens after the first sale and can improve first 30 day gross profit.",
                char_start=0,
                char_end=82,
            ),
            Chunk(
                id="continuity:0",
                chapter="continuity",
                layer="continuity",
                layers=("continuity",),
                text="Continuity adds recurring revenue after the initial transaction.",
                char_start=0,
                char_end=63,
            ),
        ]
    )


class RetrievalBackendTest(unittest.TestCase):
    def test_vector_search_uses_embeddings_and_layer_filter(self):
        index = test_index()
        results = index.vector_search(
            "customer acquisition payback",
            layer="unit-economics",
            top_k=3,
            embedding_client=FakeEmbeddingClient(),
        )

        self.assertEqual([result.chunk.id for result in results], ["payback-period:0"])
        self.assertGreater(results[0].score, 0)

    def test_hybrid_search_fuses_unique_results(self):
        index = test_index()
        results = index.hybrid_search(
            "upsell after first sale gross profit",
            top_k=3,
            embedding_client=FakeEmbeddingClient(),
        )
        ids = [result.chunk.id for result in results]

        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids[0], "upsells:0")


if __name__ == "__main__":
    unittest.main()
