import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from money_model_architect.retrieval import Chunk, SearchResult
from scripts import eval_search_query_quality as query_eval


def chunk(chunk_id: str) -> Chunk:
    return Chunk(
        id=chunk_id,
        chapter=chunk_id.split(":")[0],
        layer="unit-economics",
        layers=("unit-economics",),
        text=chunk_id,
        char_start=0,
        char_end=len(chunk_id),
    )


class SearchQueryQualityEvalTest(unittest.TestCase):
    def test_fuse_query_results_can_promote_chunks_seen_across_variants(self):
        first = [
            SearchResult(chunk=chunk("a:0"), score=10),
            SearchResult(chunk=chunk("shared:0"), score=9),
        ]
        second = [
            SearchResult(chunk=chunk("b:0"), score=10),
            SearchResult(chunk=chunk("shared:0"), score=9),
        ]

        fused = query_eval.fuse_query_results([first, second], top_k=2)

        self.assertEqual(fused[0].chunk.id, "shared:0")
        self.assertEqual(len({result.chunk.id for result in fused}), 2)


if __name__ == "__main__":
    unittest.main()
