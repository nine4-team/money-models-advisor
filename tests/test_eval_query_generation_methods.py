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
        guided_v2 = query_eval.build_prompt(self.case, "guided_model_rewrite_v2")

        self.assertIn(self.case["user_turn"], unguided)
        self.assertIn(self.case["user_turn"], guided)
        self.assertIn(self.case["user_turn"], guided_v2)
        self.assertNotIn("known_useful_chunk_ids", unguided)
        self.assertNotIn("known_useful_chunk_ids", guided)
        self.assertNotIn("known_useful_chunk_ids", guided_v2)
        self.assertNotIn("Client-financed acquisition", unguided)
        self.assertIn("Client-financed acquisition", guided)
        self.assertIn("Client-financed acquisition", guided_v2)

    def test_guided_v2_preserves_relationships_without_fixed_concept_count(self):
        guided_v1 = query_eval.build_prompt(self.case, "guided_model_rewrite")
        guided_v2 = query_eval.build_prompt(self.case, "guided_model_rewrite_v2")

        self.assertNotIn("there is no fixed number of concepts", guided_v1)
        self.assertIn("there is no fixed number of concepts", guided_v2)
        self.assertIn("mechanism, relationship, comparison, sequence, or combined system", guided_v2)
        self.assertIn("merely because\nthe guide lists it as related or nearby", guided_v2)
        self.assertEqual(
            query_eval.PROMPT_VERSIONS["guided_model_rewrite_v2"],
            "query-generation-prompt.v2",
        )

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
            {
                "case_id": "one",
                "error": None,
                "first_useful_rank": 1,
                "retrieval_latency_ms": 10,
                "useful_returned_chunk_ids": ["a", "b", "c"],
            },
            {
                "case_id": "two",
                "error": None,
                "first_useful_rank": 4,
                "retrieval_latency_ms": 20,
                "useful_returned_chunk_ids": ["d"],
            },
        ]

        summary = query_eval.score_result_rows(rows)

        self.assertEqual(summary["hit_at_1_pct"], 50.0)
        self.assertEqual(summary["hit_at_3_pct"], 50.0)
        self.assertEqual(summary["hit_at_5_pct"], 100.0)
        self.assertEqual(summary["mean_first_useful_rank"], 2.5)
        self.assertEqual(summary["useful_results"], 4)
        self.assertEqual(summary["result_slots"], 10)
        self.assertEqual(summary["mean_useful_results_at_k"], 2.0)
        self.assertEqual(summary["median_useful_results_at_k"], 2.0)
        self.assertEqual(summary["precision_at_k_pct"], 40.0)
        self.assertEqual(summary["noise_at_k_pct"], 60.0)
        self.assertEqual(summary["useful_results_per_case_distribution"], {"1": 1, "3": 1})

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

    def test_holdout_report_describes_post_run_label_audit(self):
        result = query_eval.score_result_rows(
            [{"case_id": "one", "error": None, "first_useful_rank": 1, "retrieval_latency_ms": 10}]
        )
        summary = {
            "backends": ["hybrid"],
            "case_count": 1,
            "case_splits": ["holdout"],
            "cases_file": "holdout.jsonl",
            "created_at": "2026-08-10T00:00:00Z",
            "generation": {
                "raw_question": {
                    "cases": 1,
                    "valid_cases": 1,
                    "mean_latency_ms": 0,
                    "p50_latency_ms": 0,
                    "total_codex_reported_tokens": None,
                }
            },
            "method_version": "single-query-methods.v1",
            "methods": ["raw_question"],
            "model": "gpt-5.5",
            "results": {"raw_question": {"hybrid": result}},
            "top_k": 5,
        }

        report = query_eval.render_report(summary)

        self.assertIn("1 reserved holdout cases", report)
        self.assertIn("queries and retrieval results were frozen", report)
        self.assertIn("not an independently human-adjudicated benchmark", report)
        self.assertNotIn("exposed development cases", report)

    def test_expansion_report_does_not_claim_holdout_status(self):
        result = query_eval.score_result_rows(
            [{"case_id": "one", "error": None, "first_useful_rank": 1, "retrieval_latency_ms": 10}]
        )
        summary = {
            "backends": ["hybrid"],
            "case_count": 1,
            "case_splits": ["expansion"],
            "cases_file": "expansion.jsonl",
            "created_at": "2026-08-11T00:00:00Z",
            "generation": {
                "raw_question": {
                    "cases": 1,
                    "valid_cases": 1,
                    "mean_latency_ms": 0,
                    "p50_latency_ms": 0,
                    "total_codex_reported_tokens": None,
                }
            },
            "method_version": "single-query-methods.v1",
            "methods": ["raw_question"],
            "model": "gpt-5.5",
            "results": {"raw_question": {"hybrid": result}},
            "top_k": 5,
        }

        report = query_eval.render_report(summary)

        self.assertIn("1 regression expansion cases", report)
        self.assertIn("not an unopened holdout", report)
        self.assertNotIn("reserved holdout", report)


if __name__ == "__main__":
    unittest.main()
