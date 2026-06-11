import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from money_model_architect.embeddings import OpenAIEmbeddingClient


class FakeOpenAIEmbeddingClient(OpenAIEmbeddingClient):
    def __init__(self, cache_dir: Path):
        super().__init__(api_key="test-key", cache_dir=cache_dir, model="text-embedding-3-small")
        self.requests: list[list[str]] = []

    def _request_embeddings(self, texts):
        self.requests.append(list(texts))
        return [[float(len(text)), 1.0] for text in texts]


class EmbeddingClientStatsTest(unittest.TestCase):
    def test_cache_miss_then_hit_are_counted_by_purpose(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = FakeOpenAIEmbeddingClient(Path(tmp))

            first = client.embed_texts(["alpha", "beta"], purpose="corpus")
            second = client.embed_texts(["alpha"], purpose="query")
            third = client.embed_texts(["alpha", "beta"], purpose="corpus")

            self.assertEqual(first, [[5.0, 1.0], [4.0, 1.0]])
            self.assertEqual(second, [[5.0, 1.0]])
            self.assertEqual(third, [[5.0, 1.0], [4.0, 1.0]])
            self.assertEqual(client.requests, [["alpha", "beta"]])

            stats = client.stats.to_dict()["by_purpose"]
            self.assertEqual(stats["corpus"]["cache_misses"], 2)
            self.assertEqual(stats["corpus"]["cache_hits"], 2)
            self.assertEqual(stats["corpus"]["api_batches"], 1)
            self.assertEqual(stats["corpus"]["api_inputs"], 2)
            self.assertEqual(stats["query"]["cache_hits"], 1)
            self.assertEqual(stats["query"]["cache_misses"], 0)

    def test_cache_presence_reports_completeness_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = FakeOpenAIEmbeddingClient(Path(tmp))
            client.embed_texts(["cached"], purpose="query")

            presence = client.cache_presence(["cached", "missing"])

            self.assertEqual(presence["hits"], 1)
            self.assertEqual(presence["misses"], 1)
            self.assertFalse(presence["complete"])


if __name__ == "__main__":
    unittest.main()
