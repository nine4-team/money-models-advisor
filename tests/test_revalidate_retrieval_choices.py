import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "revalidate_retrieval_choices.py"
SPEC = importlib.util.spec_from_file_location("revalidate_retrieval_choices", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RetrievalRevalidationConfigurationTests(unittest.TestCase):
    def test_historical_matrix_pins_small_embedding_configuration(self) -> None:
        client = MODULE.control_embedding_client()

        self.assertEqual(client.model, "text-embedding-3-small")
        self.assertIsNone(client.dimensions)
        self.assertEqual(client.embedding_id, "text-embedding-3-small")

    def test_active_hosted_namespace_matches_selected_large_embedding(self) -> None:
        self.assertEqual(
            MODULE.ACTIVE_PINECONE_NAMESPACE,
            "money-models-framework-large-d1536",
        )


if __name__ == "__main__":
    unittest.main()
