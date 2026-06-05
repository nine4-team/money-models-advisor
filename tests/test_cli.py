import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from money_model_architect.cli import main


def run_cli(args: list[str]) -> str:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(args)
    assert exit_code == 0
    return output.getvalue()


class CliTest(unittest.TestCase):
    def test_search_returns_source_material(self):
        output = run_cli(["search", "CAC payback", "--layer", "unit-economics", "--top-k", "1"])
        payload = json.loads(output)

        self.assertEqual(payload["query"], "CAC payback")
        self.assertEqual(payload["layer"], "unit-economics")
        self.assertEqual(len(payload["source_material"]), 1)
        self.assertIn("text", payload["source_material"][0])
        self.assertIn("id", payload["source_material"][0])

    def test_snapshot_show_and_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            show_output = run_cli(["snapshot", "--business-dir", tmp])
            empty_snapshot = json.loads(show_output)

            self.assertEqual(empty_snapshot["advisor_state"]["advisory_status"], "insufficient_context")

            set_output = run_cli(
                [
                    "snapshot",
                    "set",
                    "--business-dir",
                    tmp,
                    "economics.cac=350",
                    "business.business_type=coaching business",
                    "money_model.upsell.exists=false",
                ]
            )
            updated = json.loads(set_output)

            self.assertEqual(updated["state"]["economics"]["cac"], 350)
            self.assertEqual(updated["state"]["business"]["business_type"], "coaching business")
            self.assertFalse(updated["state"]["money_model"]["upsell"]["exists"])
            self.assertEqual(updated["state"]["field_sources"]["economics.cac"]["source_type"], "cli")

    def test_logs_summarize_saved_turns(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_cli(
                [
                    "chat",
                    "--business-dir",
                    tmp,
                    "--message",
                    "We are a coaching business. Core offer is implementation program. CAC is $350 and first-30-day gross profit is $120. I want to diagnose cash payback.",
                ]
            )
            logs_output = run_cli(["logs", "--business-dir", tmp])
            payload = json.loads(logs_output)

            self.assertEqual(len(payload["logs"]), 1)
            self.assertIn("user_message", payload["logs"][0])
            self.assertIn("assistant_message", payload["logs"][0])
            self.assertTrue(payload["logs"][0]["source_chunk_ids"])

    def test_chat_persists_clarifying_turn_for_empty_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            chat_output = run_cli(["chat", "--business-dir", tmp, "--message", "Help me diagnose my money model."])
            logs_output = run_cli(["logs", "--business-dir", tmp, "--full"])
            payload = json.loads(logs_output)

            self.assertIn("What kind of business is this?", chat_output)
            self.assertEqual(len(payload["logs"]), 1)
            self.assertEqual(payload["logs"][0]["user_message"], "Help me diagnose my money model.")
            self.assertEqual(payload["logs"][0]["assistant_message"], "What kind of business is this?")
            self.assertEqual(payload["logs"][0]["actions"], ["set problem.user_goal"])
            self.assertEqual(payload["logs"][0]["evidence"], [])
            self.assertEqual(payload["logs"][0]["retrieval_queries"], [])

    def test_chat_extracts_first_person_business_type_and_logs_diagnosis(self):
        with tempfile.TemporaryDirectory() as tmp:
            message = (
                "I run a coaching business. We sell a 6-week implementation program. "
                "CAC is $350 and first-30-day gross profit is $120. "
                "No upsell and no continuity. I want to diagnose cash payback."
            )

            chat_output = run_cli(["chat", "--business-dir", tmp, "--message", message])
            logs_output = run_cli(["logs", "--business-dir", tmp, "--full"])
            payload = json.loads(logs_output)

            self.assertIn("Diagnosis:", chat_output)
            self.assertNotIn("What kind of business is this?", chat_output)
            self.assertEqual(len(payload["logs"]), 1)
            self.assertEqual(payload["logs"][0]["snapshot"]["business"]["business_type"], "coaching business")
            self.assertTrue(payload["logs"][0]["evidence"])
            self.assertTrue(payload["logs"][0]["retrieval_queries"])


if __name__ == "__main__":
    unittest.main()
