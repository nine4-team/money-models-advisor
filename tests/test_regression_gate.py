import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import eval_advisor_answer_quality as answer_quality  # noqa: E402
import eval_source_event_traces as source_events  # noqa: E402
import eval_tool_use_judgment as tool_use  # noqa: E402
import regression_gate  # noqa: E402


class RegressionGateTest(unittest.TestCase):
    def test_gate_uses_only_stable_offline_commands(self):
        commands = [" ".join(check.command) for check in regression_gate.CHECKS]
        joined = "\n".join(commands)

        self.assertIn("eval_tool_use_judgment.py --require-all-pass", joined)
        self.assertIn("eval_source_event_traces.py --require-all-pass", joined)
        self.assertIn("eval_advisor_answer_quality.py --require-all-pass", joined)
        self.assertNotIn("run_answer_quality_codex_eval.py", joined)
        self.assertNotIn("run_source_event_codex_eval.py", joined)
        self.assertNotIn("eval_search_decision_models.py", joined)

    def test_strict_scorers_reject_missing_or_failed_results(self):
        cases = [{"case_id": "case-1"}]

        self.assertFalse(tool_use.all_cases_pass(cases, []))
        self.assertFalse(
            tool_use.all_cases_pass(
                cases,
                [SimpleNamespace(status="scored", full_sequence_pass=False)],
            )
        )
        self.assertFalse(source_events.all_cases_pass(cases, []))
        self.assertFalse(
            source_events.all_cases_pass(cases, [SimpleNamespace(status="failed")])
        )
        self.assertFalse(
            answer_quality.all_audits_pass(
                cases,
                [{
                    "current": True,
                    "valid": True,
                    "overall_pass": True,
                    "claims": 2,
                    "supported_claims": 1,
                }],
            )
        )

    def test_strict_scorers_accept_complete_passing_results(self):
        cases = [{"case_id": "case-1"}]

        self.assertTrue(
            tool_use.all_cases_pass(
                cases,
                [SimpleNamespace(status="scored", full_sequence_pass=True)],
            )
        )
        self.assertTrue(
            source_events.all_cases_pass(cases, [SimpleNamespace(status="passed")])
        )
        self.assertTrue(
            answer_quality.all_audits_pass(
                cases,
                [{
                    "current": True,
                    "valid": True,
                    "overall_pass": True,
                    "claims": 2,
                    "supported_claims": 2,
                }],
            )
        )


if __name__ == "__main__":
    unittest.main()
