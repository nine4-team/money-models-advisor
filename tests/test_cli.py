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

    def test_search_accepts_agent_source_need(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_cli(
                [
                    "snapshot",
                    "set",
                    "--business-dir",
                    tmp,
                    "business.business_type=coaching business",
                    "money_model.core_offer.description=implementation program",
                ]
            )
            source_need = {
                "intent": "teaching_evidence",
                "layers": ["unit-economics"],
                "focus_terms": ["CAC", "payback period", "gross profit"],
                "user_turn": "why do we need fulfillment cost?",
            }
            output = run_cli(
                [
                    "search",
                    "--business-dir",
                    tmp,
                    "--source-need-json",
                    json.dumps(source_need),
                    "--top-k",
                    "1",
                ]
            )
            payload = json.loads(output)

            self.assertEqual(payload["source_need"]["intent"], "teaching_evidence")
            self.assertEqual(payload["queries"][0]["layer"], "unit-economics")
            self.assertIn("CAC", payload["queries"][0]["query"])
            self.assertEqual(len(payload["source_material"]), 1)
            self.assertEqual(len(payload["source_material"][0]["chunks"]), 1)
            self.assertIn("text", payload["source_material"][0]["chunks"][0])

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

    def test_turn_record_persists_completed_agent_turn(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_events = [
                {
                    "source_need": {
                        "intent": "diagnostic_evidence",
                        "layers": ["unit-economics"],
                        "focus_terms": ["CAC", "payback period"],
                    },
                    "query": "CAC payback period coaching business",
                    "chunks": [{"id": "payback-period:0", "score": 2.3}],
                },
                {
                    "source_need": {
                        "intent": "recommendation_evidence",
                        "layers": ["upsells"],
                        "focus_terms": ["upsell", "first 30 day gross profit"],
                    },
                    "query": "upsell first 30 day gross profit coaching business",
                    "chunks": [{"id": "upsells:0", "score": 1.7}],
                }
            ]
            record_output = run_cli(
                [
                    "turn",
                    "record",
                    "--business-dir",
                    tmp,
                    "--user-message",
                    "does this mean acquisition is probably not the bottleneck?",
                    "--assistant-message",
                    "CAC is still the first thing I would quantify.",
                    "--actions-json",
                    json.dumps(["read_snapshot", "search"]),
                    "--source-events-json",
                    json.dumps(source_events),
                    "--cited-chunk-ids-json",
                    json.dumps(["payback-period:0", "upsells:0"]),
                ]
            )
            record = json.loads(record_output)
            logs_output = run_cli(["logs", "--business-dir", tmp])
            logs = json.loads(logs_output)
            full_output = run_cli(["logs", "--business-dir", tmp, "--full"])
            full_logs = json.loads(full_output)

            self.assertTrue(record["recorded"])
            self.assertEqual(record["source_event_count"], 2)
            self.assertEqual(len(logs["logs"]), 1)
            self.assertEqual(logs["logs"][0]["actions"], ["read_snapshot", "search"])
            self.assertEqual(logs["logs"][0]["source_chunk_ids"], ["payback-period:0", "upsells:0"])
            self.assertEqual(full_logs["logs"][0]["source_events"], source_events)


if __name__ == "__main__":
    unittest.main()
