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
                "query_variants": ["why cost to deliver affects gross profit CAC payback ads"],
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
            self.assertEqual(payload["source_need"]["query_variants"], ["why cost to deliver affects gross profit CAC payback ads"])
            self.assertEqual(payload["queries"][0]["layer"], "unit-economics")
            self.assertEqual(payload["queries"][0]["query"], "why cost to deliver affects gross profit CAC payback ads")
            self.assertIn("CAC", payload["queries"][1]["query"])
            self.assertEqual(len(payload["source_material"]), 2)
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

    def test_diagnose_accepts_business_dir_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_cli(
                [
                    "snapshot",
                    "set",
                    "--business-dir",
                    tmp,
                    "business.business_type=service business",
                    "economics.cac=1000",
                    "economics.first_30_day_gross_profit=10000",
                    "economics.gross_margin=0.769",
                ]
            )

            output = run_cli(["diagnose", "--business-dir", tmp])
            payload = json.loads(output)

            self.assertEqual(payload["constraint"], "gross-margin")
            self.assertEqual(payload["metrics"]["cac"], 1000)
            self.assertEqual(payload["metrics"]["first_30_day_gross_profit"], 10000)

    def test_diagnose_accepts_snapshot_file_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            snapshot_path = Path(tmp) / "economics.json"
            snapshot_path.write_text(
                json.dumps(
                    {
                        "cac": 1000,
                        "first_30_day_gross_profit": 2500,
                        "monthly_recurring_gross_profit": 0,
                    }
                ),
                encoding="utf-8",
            )

            output = run_cli(["diagnose", "--snapshot", str(snapshot_path)])
            payload = json.loads(output)

            self.assertEqual(payload["constraint"], "scale-ready")
            self.assertEqual(payload["metrics"]["cfa_level"], 3)

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

    def test_session_start_returns_agent_workbench(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_cli(
                [
                    "snapshot",
                    "set",
                    "--business-dir",
                    tmp,
                    "business.business_type=coaching business",
                    "economics.cac=350",
                ]
            )
            run_cli(
                [
                    "turn",
                    "record",
                    "--business-dir",
                    tmp,
                    "--user-message",
                    "why do we need fulfillment cost?",
                    "--assistant-message",
                    "Because gross profit controls payback.",
                    "--actions-json",
                    json.dumps(["read_snapshot"]),
                ]
            )

            output = run_cli(
                [
                    "session",
                    "start",
                    "--business-dir",
                    tmp,
                    "--user-message",
                    "what should we do next?",
                ]
            )
            payload = json.loads(output)

            self.assertEqual(payload["user_message"], "what should we do next?")
            self.assertEqual(payload["advisor_state"]["advisory_status"], "insufficient_context")
            self.assertEqual(payload["advisor_state"]["known_facts"]["business.business_type"], "coaching business")
            self.assertEqual(payload["advisor_state"]["known_facts"]["economics.cac"], 350)
            self.assertIn("economics.first_30_day_gross_profit", payload["advisor_state"]["missing_fields"])
            self.assertEqual(payload["recent_turns"][0]["user_message"], "why do we need fulfillment cost?")
            self.assertIn("turn_record", payload["available_operations"])
            self.assertIn("agent_owns", payload["boundary"])

    def test_session_start_rejects_advisor_repo_as_business_dir(self):
        repo_root = Path(__file__).resolve().parents[1]
        with self.assertRaises(SystemExit):
            run_cli(["session", "start", "--business-dir", str(repo_root), "--user-message", "hello"])

    def test_session_finish_records_validated_turn_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            record_artifact = {
                "user_message": "what should we do next?",
                "assistant_message": "I would fix payback first.",
                "actions": ["session_start", "read_snapshot", "search_source_material", "answer"],
                "source_events": [
                    {
                        "source_need": {
                            "intent": "diagnostic_evidence",
                            "layers": ["unit-economics"],
                            "focus_terms": ["CAC", "gross profit", "payback period"],
                            "user_turn": "what should we do next?",
                            "query_variants": [
                                "CAC gross profit payback period",
                                "customer acquisition cost first month gross profit",
                            ],
                        },
                        "queries": [
                            "CAC gross profit payback period",
                            "customer acquisition cost first month gross profit",
                        ],
                        "chunks": [{"id": "payback-period:0", "score": 20.4}],
                    }
                ],
                "cited_chunk_ids": ["payback-period:0"],
                "metadata": {"run_type": "unit_test"},
            }

            output = run_cli(
                [
                    "session",
                    "finish",
                    "--business-dir",
                    tmp,
                    "--record-json",
                    json.dumps(record_artifact),
                ]
            )
            payload = json.loads(output)
            full_logs = json.loads(run_cli(["logs", "--business-dir", tmp, "--full"]))

            self.assertTrue(payload["recorded"])
            self.assertEqual(payload["warnings"], [])
            self.assertEqual(payload["source_event_count"], 1)
            self.assertEqual(payload["cited_chunk_ids"], ["payback-period:0"])
            self.assertEqual(full_logs["logs"][0]["actions"], record_artifact["actions"])
            self.assertEqual(full_logs["logs"][0]["metadata"], {"run_type": "unit_test"})
            self.assertEqual(full_logs["logs"][0]["source_events"][0]["query"], "CAC gross profit payback period")

    def test_session_finish_warns_when_inspected_chunks_are_not_cited(self):
        with tempfile.TemporaryDirectory() as tmp:
            record_artifact = {
                "user_message": "teach me payback",
                "assistant_message": "Payback is about recovering CAC.",
                "actions": ["session_start", "search_source_material", "answer"],
                "source_events": [
                    {
                        "source_need": {
                            "intent": "teaching_evidence",
                            "layers": ["unit-economics"],
                            "focus_terms": ["payback period"],
                            "query_variants": [
                                "payback period recover CAC",
                                "customer acquisition cost payback",
                            ],
                        },
                        "queries": [
                            "payback period recover CAC",
                            "customer acquisition cost payback",
                        ],
                        "chunks": [{"id": "payback-period:0"}],
                    }
                ],
            }

            output = run_cli(
                [
                    "session",
                    "finish",
                    "--business-dir",
                    tmp,
                    "--record-json",
                    json.dumps(record_artifact),
                ]
            )
            payload = json.loads(output)

            self.assertEqual(payload["warnings"], ["source_events include inspected chunks but cited_chunk_ids is empty"])

    def test_session_finish_rejects_unknown_cited_chunk(self):
        with tempfile.TemporaryDirectory() as tmp:
            record_artifact = {
                "user_message": "teach me payback",
                "assistant_message": "Payback is about recovering CAC.",
                "actions": ["session_start", "search_source_material", "answer"],
                "source_events": [
                    {
                        "source_need": {
                            "intent": "teaching_evidence",
                            "layers": ["unit-economics"],
                            "focus_terms": ["payback period"],
                            "query_variants": [
                                "payback period recover CAC",
                                "customer acquisition cost payback",
                            ],
                        },
                        "queries": ["payback period"],
                        "chunks": [{"id": "payback-period:0"}],
                    }
                ],
                "cited_chunk_ids": ["missing:0"],
            }

            with self.assertRaises(SystemExit):
                run_cli(
                    [
                        "session",
                        "finish",
                        "--business-dir",
                        tmp,
                        "--record-json",
                        json.dumps(record_artifact),
                    ]
                )

    def test_session_finish_records_calculation_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            record_artifact = {
                "user_message": "if CAC is 1000 and first month gross profit is 10000, what's payback?",
                "assistant_message": "Payback is 0.1 months.",
                "actions": ["session_start", "read_snapshot", "calculate", "answer"],
                "calculation_events": [
                    {
                        "metric": "payback",
                        "inputs": {"cac": 1000, "month_one_gp": 10000, "monthly_recurring_gp": 0},
                        "value": 0.1,
                    }
                ],
            }

            output = run_cli(
                [
                    "session",
                    "finish",
                    "--business-dir",
                    tmp,
                    "--record-json",
                    json.dumps(record_artifact),
                ]
            )
            payload = json.loads(output)
            full_logs = json.loads(run_cli(["logs", "--business-dir", tmp, "--full"]))
            logs = json.loads(run_cli(["logs", "--business-dir", tmp]))

            self.assertTrue(payload["recorded"])
            self.assertEqual(payload["calculation_event_count"], 1)
            self.assertEqual(full_logs["logs"][0]["calculation_events"], record_artifact["calculation_events"])
            self.assertEqual(logs["logs"][0]["calculation_events"], record_artifact["calculation_events"])

    def test_session_finish_rejects_missing_calculation_event_for_calculate_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            record_artifact = {
                "user_message": "calculate payback",
                "assistant_message": "Payback is 0.1 months.",
                "actions": ["session_start", "calculate", "answer"],
            }

            with self.assertRaises(SystemExit):
                run_cli(
                    [
                        "session",
                        "finish",
                        "--business-dir",
                        tmp,
                        "--record-json",
                        json.dumps(record_artifact),
                    ]
                )

    def test_session_finish_rejects_source_event_without_query_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            record_artifact = {
                "user_message": "teach me payback",
                "assistant_message": "Payback is about recovering CAC.",
                "actions": ["session_start", "search_source_material", "answer"],
                "source_events": [
                    {
                        "source_need": {
                            "intent": "teaching_evidence",
                            "layers": ["unit-economics"],
                            "focus_terms": ["payback period"],
                        },
                        "queries": ["payback period"],
                        "chunks": [{"id": "payback-period:0"}],
                    }
                ],
            }

            with self.assertRaises(SystemExit):
                run_cli(
                    [
                        "session",
                        "finish",
                        "--business-dir",
                        tmp,
                        "--record-json",
                        json.dumps(record_artifact),
                    ]
                )

    def test_session_finish_rejects_unexecuted_query_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            record_artifact = {
                "user_message": "teach me payback",
                "assistant_message": "Payback is about recovering CAC.",
                "actions": ["session_start", "search_source_material", "answer"],
                "source_events": [
                    {
                        "source_need": {
                            "intent": "teaching_evidence",
                            "layers": ["unit-economics"],
                            "focus_terms": ["payback period"],
                            "query_variants": [
                                "payback period recover CAC",
                                "customer acquisition cost payback",
                            ],
                        },
                        "queries": ["payback period recover CAC"],
                        "chunks": [{"id": "payback-period:0"}],
                    }
                ],
            }

            with self.assertRaises(SystemExit):
                run_cli(
                    [
                        "session",
                        "finish",
                        "--business-dir",
                        tmp,
                        "--record-json",
                        json.dumps(record_artifact),
                    ]
                )


if __name__ == "__main__":
    unittest.main()
