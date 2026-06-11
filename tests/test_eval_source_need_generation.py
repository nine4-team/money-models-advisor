import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from scripts import eval_source_need_generation as source_need_eval


class SourceNeedGenerationEvalTest(unittest.TestCase):
    def test_acceptable_intents_match_when_actual_uses_allowed_alternative(self):
        case = {
            "case_id": "case",
            "split": "dev",
            "expected_search": True,
            "expected_source_need": {
                "intent": "teaching_evidence",
                "layers": ["offers"],
                "focus_terms": ["free trial"],
            },
            "acceptable_intents": ["teaching_evidence", "recommendation_evidence"],
        }
        run = {
            "source_search_decision": True,
            "source_need": {
                "intent": "recommendation_evidence",
                "layers": ["offers"],
                "focus_terms": ["free trial"],
            },
        }

        with TemporaryDirectory() as tmpdir:
            run_path = Path(tmpdir) / "run.json"
            run_path.write_text(source_need_eval.json.dumps(run), encoding="utf-8")
            result = source_need_eval.score_case(case, run_path)

        self.assertTrue(result.intent_match)

    def test_acceptable_intents_must_include_expected_intent(self):
        errors = source_need_eval.validate_cases(
            [
                {
                    "case_id": "case",
                    "split": "dev",
                    "scenario_id": "scenario",
                    "conversation_context": "context",
                    "snapshot_fixture_path": "evals/fixtures/snapshots/1584_empty.json",
                    "prior_sessions_fixture_path": None,
                    "user_turn": "turn",
                    "expected_search": True,
                    "expected_source_need": {
                        "intent": "teaching_evidence",
                        "layers": ["offers"],
                        "focus_terms": ["free trial"],
                    },
                    "acceptable_intents": ["recommendation_evidence"],
                    "label_rationale": "rationale",
                    "ambiguity": "medium",
                    "severity_if_wrong": "medium",
                }
            ]
        )

        self.assertTrue(any("acceptable_intents must include" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
