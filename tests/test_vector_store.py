import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from money_model_architect.vector_store import (
    LocalVectorStore,
    PineconeVectorStore,
    VectorRecord,
    chunk_id_from_vector_id,
    vector_id,
)


class CapturingPineconeVectorStore(PineconeVectorStore):
    def __init__(self):
        super().__init__(
            api_key="test-key",
            index_host="https://example-index.svc.test",
            namespace="test-namespace",
        )
        self.requests = []

    def _request(self, method, path, payload):
        self.requests.append((method, path, payload))
        if path == "/query":
            return {
                "matches": [
                    {
                        "id": "heading-aware:text-embedding-3-small:cac:0",
                        "score": 0.98,
                        "metadata": {"chunk_id": "cac:0", "layers": ["unit-economics"]},
                    }
                ]
            }
        return {"upsertedCount": len(payload.get("vectors", []))}


class VectorStoreTest(unittest.TestCase):
    def test_local_vector_store_filters_and_ranks(self):
        store = LocalVectorStore(
            [
                VectorRecord(
                    id="a",
                    values=[1.0, 0.0],
                    metadata={"layers": ["unit-economics"], "chunk_id": "a:0"},
                ),
                VectorRecord(
                    id="b",
                    values=[0.0, 1.0],
                    metadata={"layers": ["upsells"], "chunk_id": "b:0"},
                ),
            ]
        )

        matches = store.query(
            [1.0, 0.0],
            top_k=2,
            filter={"layers": {"$in": ["unit-economics"]}},
        )

        self.assertEqual([match.id for match in matches], ["a"])
        self.assertEqual(matches[0].metadata["chunk_id"], "a:0")

    def test_vector_ids_round_trip_chunk_id(self):
        record_id = vector_id(
            chunking_strategy="heading-aware",
            embedding_model="text-embedding-3-small",
            chunk_id="payback-period:1",
        )

        self.assertEqual(record_id, "heading-aware:text-embedding-3-small:payback-period:1")
        self.assertEqual(chunk_id_from_vector_id(record_id), "payback-period:1")

    def test_pinecone_store_builds_upsert_and_query_payloads(self):
        store = CapturingPineconeVectorStore()

        upserted = store.upsert(
            [
                VectorRecord(
                    id="heading-aware:text-embedding-3-small:cac:0",
                    values=[0.1, 0.2],
                    metadata={"chunk_id": "cac:0", "layers": ["unit-economics"]},
                )
            ]
        )
        matches = store.query(
            [0.1, 0.2],
            top_k=5,
            filter={"layers": {"$in": ["unit-economics"]}},
        )

        self.assertEqual(upserted, 1)
        self.assertEqual(store.requests[0][1], "/vectors/upsert")
        self.assertEqual(store.requests[0][2]["namespace"], "test-namespace")
        self.assertEqual(store.requests[0][2]["vectors"][0]["metadata"]["chunk_id"], "cac:0")
        self.assertEqual(store.requests[1][1], "/query")
        self.assertEqual(store.requests[1][2]["topK"], 5)
        self.assertTrue(store.requests[1][2]["includeMetadata"])
        self.assertEqual(matches[0].metadata["chunk_id"], "cac:0")


if __name__ == "__main__":
    unittest.main()
