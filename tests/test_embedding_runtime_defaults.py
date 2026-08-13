import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from money_model_architect.embeddings import OpenAIEmbeddingClient
from money_model_architect.vector_store import PineconeVectorStore


class EmbeddingRuntimeDefaultsTest(unittest.TestCase):
    def test_selected_embedding_model_and_dimensions_are_runtime_defaults(self):
        with patch.dict(
            "os.environ",
            {},
            clear=True,
        ):
            client = OpenAIEmbeddingClient(api_key="test-key")

        self.assertEqual(client.model, "text-embedding-3-large")
        self.assertEqual(client.dimensions, 1536)

    def test_selected_model_uses_isolated_pinecone_namespace(self):
        with patch.dict("os.environ", {}, clear=True):
            store = PineconeVectorStore(api_key="test-key", index_host="example.test")

        self.assertEqual(store.default_namespace, "money-models-framework-large-d1536")


if __name__ == "__main__":
    unittest.main()
