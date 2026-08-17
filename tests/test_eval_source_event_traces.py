import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import eval_source_event_traces as source_event_eval


def write_run(tmpdir: str, payload: dict) -> Path:
    path = Path(tmpdir) / "run.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def expected(job: str, *concepts: list[str]) -> dict:
    return {"job": job, "required_query_concepts": list(concepts)}


def event(user_turn: str, query: str, *, intent: str = "diagnostic_evidence") -> dict:
    return {
        "search_request": {"intent": intent, "user_turn": user_turn, "query": query},
        "queries": [query],
        "chunks": [{"id": "chunk:0"}],
    }


class SourceEventTraceEvalTest(unittest.TestCase):
    def test_current_contract_multi_job_trace_passes(self):
        case = {
            "case_id": "case",
            "split": "dev",
            "user_turn": "what should we fix?",
            "expected_source_events": [
                expected("economics", ["CAC", "customer acquisition cost"], ["payback"]),
                expected("offer", ["front-end offer", "attraction offer"], ["paid acquisition"]),
            ],
        }
        run = {"source_events": [
            event(case["user_turn"], "customer acquisition cost gross profit payback"),
            event(case["user_turn"], "front-end offer paid acquisition", intent="recommendation_evidence"),
        ]}
        with TemporaryDirectory() as tmpdir:
            result = source_event_eval.score_case(case, write_run(tmpdir, run))
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.matched_event_count, 2)

    def test_non_current_search_contract_fails(self):
        case = {"case_id": "case", "split": "dev", "user_turn": "teach me", "expected_source_events": [expected("teach", ["offer"])]}
        run = {"source_events": [{"legacy_request": {"intent": "teaching_evidence"}, "chunks": [{"id": "x"}]}]}
        with TemporaryDirectory() as tmpdir:
            result = source_event_eval.score_case(case, write_run(tmpdir, run))
        self.assertEqual(result.status, "failed")
        self.assertIn("current_contract_missing:teach", result.failure_reasons)

    def test_query_must_preserve_all_required_concepts(self):
        case = {"case_id": "case", "split": "dev", "user_turn": "question", "expected_source_events": [expected("job", ["upsell"], ["gross profit"])]}
        run = {"source_events": [event("question", "upsell offers")]}
        with TemporaryDirectory() as tmpdir:
            result = source_event_eval.score_case(case, write_run(tmpdir, run))
        self.assertEqual(result.status, "failed")
        self.assertIn("query_concept_miss:job:0.500", result.failure_reasons)

    def test_executed_query_must_equal_search_request_query(self):
        case = {"case_id": "case", "split": "dev", "user_turn": "question", "expected_source_events": [expected("job", ["payback"])]}
        bad = event("question", "payback")
        bad["queries"] = ["different query"]
        with TemporaryDirectory() as tmpdir:
            result = source_event_eval.score_case(case, write_run(tmpdir, {"source_events": [bad]}))
        self.assertEqual(result.status, "failed")
        self.assertIn("query_not_executed:job", result.failure_reasons)

    def test_extra_event_is_a_failure(self):
        case = {"case_id": "case", "split": "dev", "user_turn": "question", "expected_source_events": [expected("job", ["payback"])]}
        run = {"source_events": [event("question", "payback"), event("question", "continuity recurring")]}
        with TemporaryDirectory() as tmpdir:
            result = source_event_eval.score_case(case, write_run(tmpdir, run))
        self.assertEqual(result.status, "failed")
        self.assertIn("extra_events:1", result.failure_reasons)

    def test_no_search_case_requires_no_events(self):
        case = {"case_id": "case", "split": "dev", "user_turn": "question", "expected_source_events": []}
        with TemporaryDirectory() as tmpdir:
            passed = source_event_eval.score_case(case, write_run(tmpdir, {"source_events": []}))
            failed = source_event_eval.score_case(case, write_run(tmpdir, {"source_events": [event("question", "payback")]}))
        self.assertEqual(passed.status, "passed")
        self.assertEqual(failed.failure_reasons, ("unexpected_source_events:1",))

    def test_dataset_validates(self):
        cases = source_event_eval.load_jsonl(Path("evals/advisor_source_event_cases.jsonl"))
        self.assertEqual(source_event_eval.validate_cases(cases), [])


if __name__ == "__main__":
    unittest.main()
