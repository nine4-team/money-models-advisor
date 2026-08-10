import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts import eval_query_generation_methods as query_eval


class QueryGenerationMethodEvalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = query_eval.load_jsonl(query_eval.DEFAULT_CASES)[0]

    def test_visible_snapshot_excludes_advisor_state_and_field_sources(self):
        visible = query_eval.generator_visible_snapshot(ROOT / self.case["snapshot_fixture_path"])

        self.assertEqual(set(visible), {"business", "money_model", "economics", "problem"})
        self.assertNotIn("advisor_state", visible)
        self.assertNotIn("field_sources", visible)
        self.assertFalse(visible["money_model"]["continuity"]["exists"])
        self.assertEqual(visible["economics"]["monthly_recurring_gross_profit"], 0)
        self.assertNotIn("lifetime_gross_profit", visible["economics"])

    def test_guided_and_unguided_prompts_share_input_without_label_leakage(self):
        unguided = query_eval.build_prompt(self.case, "model_rewrite")
        guided = query_eval.build_prompt(self.case, "guided_model_rewrite")

        self.assertIn(self.case["user_turn"], unguided)
        self.assertIn(self.case["user_turn"], guided)
        self.assertNotIn("known_useful_chunk_ids", unguided)
        self.assertNotIn("known_useful_chunk_ids", guided)
        self.assertNotIn("Client-financed acquisition", unguided)
        self.assertIn("Client-financed acquisition", guided)

    def test_raw_query_is_only_transport_normalized(self):
        case = {"user_turn": "  why   does this work?  "}
        self.assertEqual(query_eval.raw_query(case), "why does this work?")

    def test_validate_query_rejects_multiline_or_empty_output(self):
        with self.assertRaises(ValueError):
            query_eval.validate_query("")
        with self.assertRaises(ValueError):
            query_eval.validate_query("one\ntwo")

    def test_first_useful_rank_and_summary(self):
        self.assertEqual(query_eval.first_useful_rank(["a", "b"], {"b"}), 2)
        self.assertIsNone(query_eval.first_useful_rank(["a"], {"b"}))
        rows = [
            {"case_id": "one", "error": None, "first_useful_rank": 1, "retrieval_latency_ms": 10},
            {"case_id": "two", "error": None, "first_useful_rank": 4, "retrieval_latency_ms": 20},
        ]

        summary = query_eval.score_result_rows(rows)

        self.assertEqual(summary["hit_at_1_pct"], 50.0)
        self.assertEqual(summary["hit_at_3_pct"], 50.0)
        self.assertEqual(summary["hit_at_5_pct"], 100.0)
        self.assertEqual(summary["mean_first_useful_rank"], 2.5)

    def test_quality_rates_exclude_infrastructure_errors_but_report_coverage(self):
        rows = [
            {"case_id": "one", "error": None, "first_useful_rank": 1, "retrieval_latency_ms": 10},
            {
                "case_id": "two",
                "error": "missing_retrieval_artifact",
                "first_useful_rank": None,
                "retrieval_latency_ms": 0,
            },
        ]

        summary = query_eval.score_result_rows(rows)

        self.assertEqual(summary["completed_cases"], 1)
        self.assertEqual(summary["coverage_pct"], 50.0)
        self.assertEqual(summary["hit_at_1_pct"], 100.0)
        self.assertEqual(summary["execution_errors"], 1)
        self.assertEqual(summary["missing_cases"], ["two"])


if __name__ == "__main__":
    unittest.main()
