import sys
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import capture_tool_use_trace as capture  # noqa: E402
import eval_search_decision_models as gate_eval  # noqa: E402
import eval_tool_use_judgment as tool_eval  # noqa: E402


CASES_PATH = ROOT / "evals" / "advisor_search_decision_cases.jsonl"


class SearchDecisionEvalTest(unittest.TestCase):
    def test_dataset_is_balanced_by_label_and_context(self):
        cases = tool_eval.load_jsonl(CASES_PATH)
        self.assertEqual(gate_eval.validate_cases(cases), [])
        self.assertEqual(len(cases), 48)
        labels = Counter("search" if "search_source_material" in case["required_actions"] else "no_search" for case in cases)
        self.assertEqual(labels, {"search": 24, "no_search": 24})

        by_scenario = defaultdict(Counter)
        for case in cases:
            label = "search" if "search_source_material" in case["required_actions"] else "no_search"
            by_scenario[case["scenario_id"]][label] += 1
        self.assertEqual(set(by_scenario), {"1584_design", "saas_retention", "fitness_coaching", "ecommerce_skincare", "b2b_consulting"})
        for counts in by_scenario.values():
            self.assertEqual(counts["search"], counts["no_search"])

    def test_acting_prompt_hides_evaluator_context_and_labels(self):
        case = tool_eval.load_jsonl(CASES_PATH)[0]
        prompt = capture.render_acting_prompt(case, Path("/tmp/business"))
        for field in (
            "conversation_context",
            "scenario_id",
            "turn_type",
            "required_actions",
            "forbidden_actions",
            "search_allowed",
            "label_rationale",
        ):
            self.assertNotIn(field, prompt)
        self.assertIn(case["user_turn"], prompt)

    def test_isolated_gate_runtime_has_no_case_labels_or_prior_runs(self):
        case = tool_eval.load_jsonl(CASES_PATH)[0]
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            gate_eval.copy_runtime(runtime)
            business_dir = gate_eval.prepare_business_dir(case, runtime)
            context = gate_eval.load_business_context(runtime, business_dir, case["user_turn"])
            prompt = gate_eval.acting_prompt(case["user_turn"], runtime, context)
            files = {str(path.relative_to(runtime)) for path in runtime.rglob("*") if path.is_file()}

            self.assertNotIn(case["case_id"], prompt)
            self.assertNotIn("search_allowed", prompt)
            self.assertFalse(any("advisor_search_decision_cases" in path for path in files))
            self.assertFalse(any("/reports/" in f"/{path}" for path in files))
            self.assertFalse(any("/runs/" in f"/{path}" for path in files))
            self.assertIn(gate_eval.search_gate_rules(), prompt)


if __name__ == "__main__":
    unittest.main()
