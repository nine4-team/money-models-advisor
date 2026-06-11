import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import eval_source_event_traces as source_event_eval


def write_run(tmpdir: str, payload: dict) -> Path:
    path = Path(tmpdir) / "run.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class SourceEventTraceEvalTest(unittest.TestCase):
    def test_multi_source_trace_passes_when_events_are_split(self):
        case = {
            "case_id": "case",
            "split": "dev",
            "expected_source_events": [
                {
                    "intent": "diagnostic_evidence",
                    "layers": ["unit-economics"],
                    "focus_terms": ["CAC", "payback period"],
                },
                {
                    "intent": "recommendation_evidence",
                    "layers": ["upsells"],
                    "focus_terms": ["upsell", "first 30 day gross profit"],
                },
            ],
        }
        run = {
            "source_events": [
                {
                    "source_need": {
                        "intent": "diagnostic_evidence",
                        "layers": ["unit-economics"],
                        "focus_terms": ["CAC", "payback period", "gross margin"],
                    },
                    "chunks": [{"id": "payback-period:0"}],
                },
                {
                    "source_need": {
                        "intent": "recommendation_evidence",
                        "layers": ["upsells"],
                        "focus_terms": ["upsell", "first 30 day gross profit"],
                    },
                    "chunks": [{"id": "upsells:0"}],
                },
            ]
        }

        with TemporaryDirectory() as tmpdir:
            result = source_event_eval.score_case(case, write_run(tmpdir, run))

        self.assertEqual(result.status, "passed")
        self.assertTrue(result.all_expected_events_matched)
        self.assertEqual(result.matched_event_count, 2)

    def test_single_broad_source_event_fails_multi_source_trace(self):
        case = {
            "case_id": "case",
            "split": "dev",
            "expected_source_events": [
                {
                    "intent": "diagnostic_evidence",
                    "layers": ["unit-economics"],
                    "focus_terms": ["CAC", "payback period"],
                },
                {
                    "intent": "recommendation_evidence",
                    "layers": ["upsells"],
                    "focus_terms": ["upsell", "first 30 day gross profit"],
                },
            ],
        }
        run = {
            "source_events": [
                {
                    "source_need": {
                        "intent": "recommendation_evidence",
                        "layers": ["unit-economics", "offers", "upsells"],
                        "focus_terms": ["CAC", "payback period", "upsell", "first 30 day gross profit"],
                    },
                    "chunks": [{"id": "payback-period:0"}],
                }
            ]
        }

        with TemporaryDirectory() as tmpdir:
            result = source_event_eval.score_case(case, write_run(tmpdir, run))

        self.assertEqual(result.status, "failed")
        self.assertFalse(result.all_expected_events_matched)
        self.assertIn("missing_intent:diagnostic_evidence", result.failure_reasons)

    def test_inspected_chunks_count_as_chunk_evidence(self):
        case = {
            "case_id": "case",
            "split": "dev",
            "expected_source_events": [
                {
                    "intent": "diagnostic_evidence",
                    "layers": ["unit-economics"],
                    "focus_terms": ["CAC", "payback period"],
                }
            ],
        }
        run = {
            "source_events": [
                {
                    "source_need": {
                        "intent": "diagnostic_evidence",
                        "layers": ["unit-economics"],
                        "focus_terms": ["CAC", "payback period"],
                    },
                    "inspected_chunks": [{"id": "payback-period:0"}],
                }
            ]
        }

        with TemporaryDirectory() as tmpdir:
            result = source_event_eval.score_case(case, write_run(tmpdir, run))

        self.assertEqual(result.status, "passed")

    def test_focus_matching_normalizes_punctuation(self):
        case = {
            "case_id": "case",
            "split": "dev",
            "expected_source_events": [
                {
                    "intent": "recommendation_evidence",
                    "layers": ["offers"],
                    "focus_terms": ["front-end offer", "paid acquisition"],
                }
            ],
        }
        run = {
            "source_events": [
                {
                    "source_need": {
                        "intent": "recommendation_evidence",
                        "layers": ["offers"],
                        "focus_terms": ["front end offer", "paid acquisition test"],
                    },
                    "chunks": [{"id": "make-your-money-model:0"}],
                }
            ]
        }

        with TemporaryDirectory() as tmpdir:
            result = source_event_eval.score_case(case, write_run(tmpdir, run))

        self.assertEqual(result.status, "passed")

    def test_extra_source_events_are_warnings_not_failures(self):
        case = {
            "case_id": "case",
            "split": "dev",
            "expected_source_events": [
                {
                    "intent": "diagnostic_evidence",
                    "layers": ["unit-economics"],
                    "focus_terms": ["CAC", "payback period"],
                }
            ],
        }
        run = {
            "source_events": [
                {
                    "source_need": {
                        "intent": "diagnostic_evidence",
                        "layers": ["unit-economics"],
                        "focus_terms": ["CAC", "payback period"],
                    },
                    "chunks": [{"id": "payback-period:0"}],
                },
                {
                    "source_need": {
                        "intent": "recommendation_evidence",
                        "layers": ["offers"],
                        "focus_terms": ["front end offer"],
                    },
                    "chunks": [{"id": "make-your-money-model:0"}],
                },
            ]
        }

        with TemporaryDirectory() as tmpdir:
            result = source_event_eval.score_case(case, write_run(tmpdir, run))

        self.assertEqual(result.status, "passed")
        self.assertEqual(result.warning_reasons, ("extra_events:1",))

    def test_no_search_case_passes_with_no_source_events(self):
        case = {
            "case_id": "case",
            "split": "dev",
            "expected_source_events": [],
        }
        run = {"source_events": []}

        with TemporaryDirectory() as tmpdir:
            result = source_event_eval.score_case(case, write_run(tmpdir, run))

        self.assertEqual(result.status, "passed")
        self.assertTrue(result.all_expected_events_matched)

    def test_no_search_case_fails_with_any_source_event(self):
        case = {
            "case_id": "case",
            "split": "dev",
            "expected_source_events": [],
        }
        run = {
            "source_events": [
                {
                    "source_need": {
                        "intent": "teaching_evidence",
                        "layers": ["offers"],
                        "focus_terms": ["front end offer"],
                    },
                    "chunks": [{"id": "make-your-money-model:0"}],
                }
            ]
        }

        with TemporaryDirectory() as tmpdir:
            result = source_event_eval.score_case(case, write_run(tmpdir, run))

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.failure_reasons, ("unexpected_source_events:1",))

    def test_validate_cases_allows_empty_expected_source_events(self):
        errors = source_event_eval.validate_cases(
            [
                {
                    "case_id": "case",
                    "split": "dev",
                    "scenario_id": "scenario",
                    "conversation_context": "context",
                    "snapshot_fixture_path": "evals/fixtures/snapshots/1584_empty.json",
                    "prior_sessions_fixture_path": None,
                    "user_turn": "turn",
                    "expected_source_events": [],
                    "label_rationale": "rationale",
                    "ambiguity": "medium",
                    "severity_if_wrong": "medium",
                }
            ]
        )

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
