import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from money_model_architect.retrieval import Chunk, CorpusIndex, tokenize
from money_model_architect.vector_store import VectorMatch, subject_namespace


class FakeEmbeddingClient:
    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str], *, purpose: str = "query") -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        lowered = text.lower()
        return [
            float("cac" in lowered or "acquisition" in lowered),
            float("payback" in lowered),
            float("upsell" in lowered),
            float("continuity" in lowered or "recurring" in lowered),
        ]


class CapturingVectorStore:
    name = "capture"

    def __init__(self):
        self.requested_top_k = None

    def query(self, vector, *, top_k, namespace=None, filter=None):
        self.requested_top_k = top_k
        return [
            VectorMatch(
                id="payback-period:0",
                score=0.9,
                metadata={"chunk_id": "payback-period:0", "subjects": ["unit-economics"]},
            )
        ]


def test_index() -> CorpusIndex:
    return CorpusIndex(
        [
            Chunk(
                id="payback-period:0",
                chapter="payback-period",
                subject="unit-economics",
                subjects=("unit-economics",),
                text="CAC and payback period determine whether acquisition is recovered.",
                char_start=0,
                char_end=72,
            ),
            Chunk(
                id="upsells:0",
                chapter="upsells",
                subject="upsells",
                subjects=("upsells",),
                text="An upsell happens after the first sale and can improve first 30 day gross profit.",
                char_start=0,
                char_end=82,
            ),
            Chunk(
                id="continuity:0",
                chapter="continuity",
                subject="continuity",
                subjects=("continuity",),
                text="Continuity adds recurring revenue after the initial transaction.",
                char_start=0,
                char_end=63,
            ),
        ]
    )


class RetrievalBackendTest(unittest.TestCase):
    def test_framework_aware_is_the_runtime_default(self):
        self.assertEqual(CorpusIndex([]).strategy.name, "framework-aware")

    def test_framework_aware_corpus_has_no_thousand_word_chunks(self):
        corpus = Path(__file__).resolve().parents[1] / "corpus" / "transcripts"
        index = CorpusIndex.from_transcripts(corpus)

        self.assertLess(max(len(tokenize(chunk.text)) for chunk in index.chunks), 1000)

    def test_vector_search_uses_embeddings_and_subject_filter(self):
        index = test_index()
        results = index.vector_search(
            "customer acquisition payback",
            subject="unit-economics",
            top_k=3,
            embedding_client=FakeEmbeddingClient(),
        )

        self.assertEqual([result.chunk.id for result in results], ["payback-period:0"])
        self.assertGreater(results[0].score, 0)

    def test_vector_search_uses_explicit_subject_namespaces(self):
        index = test_index()
        results = index.vector_search(
            "customer acquisition payback",
            subjects=("unit-economics",),
            top_k=3,
            embedding_client=FakeEmbeddingClient(),
            vector_namespaces=(subject_namespace("unit-economics"),),
        )

        self.assertEqual([result.chunk.id for result in results], ["payback-period:0"])

    def test_vector_search_does_not_overfetch_beyond_candidate_depth(self):
        index = test_index()
        store = CapturingVectorStore()

        index.vector_search(
            "customer acquisition payback",
            top_k=7,
            embedding_client=FakeEmbeddingClient(),
            vector_store=store,
        )

        self.assertEqual(store.requested_top_k, 7)

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
