import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_answer_quality_codex_eval as answer_eval  # noqa: E402
import eval_advisor_answer_quality as answer_scorer  # noqa: E402


CASES_PATH = ROOT / "evals" / "advisor_answer_quality_cases.jsonl"
SOURCE_CASES_PATH = ROOT / "evals" / "advisor_search_decision_cases.jsonl"
MANIFEST_PATH = ROOT / "evals" / "answer_quality_suite_v1_manifest.json"
FINAL_AUDIT_PATH = ROOT / "evals" / "advisor_answer_quality_expanded_final_audit.jsonl"
FINAL_RUNS_PATH = ROOT / "evals" / "runs" / "answer_quality" / "expanded_v1_final"


class AnswerQualityExpansionTest(unittest.TestCase):
    def test_selection_is_balanced_and_reuses_frozen_source_cases(self):
        cases = answer_eval.load_jsonl(CASES_PATH)
        source_cases = {case["case_id"]: case for case in answer_eval.load_jsonl(SOURCE_CASES_PATH)}
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

        self.assertEqual(answer_eval.validate_cases(cases), [])
        self.assertEqual(len(cases), 20)
        self.assertEqual(Counter(case["scenario_id"] for case in cases), {
            "1584_design": 4,
            "saas_retention": 4,
            "fitness_coaching": 4,
            "ecommerce_skincare": 4,
            "b2b_consulting": 4,
        })
        self.assertEqual(Counter(case["answer_category"] for case in cases), {
            "source_grounded": 10,
            "calculation": 5,
            "clarification": 5,
        })
        self.assertEqual(
            [case["source_case_id"] for case in cases],
            manifest["selected_case_ids"],
        )
        for case in cases:
            source = source_cases[case["source_case_id"]]
            self.assertEqual(case["user_turn"], source["user_turn"])
            self.assertEqual(case["snapshot_fixture_path"], source["snapshot_fixture_path"])

    def test_sanitized_runtime_excludes_evaluation_artifacts(self):
        case = answer_eval.load_jsonl(CASES_PATH)[0]
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            answer_eval.copy_runtime(runtime, openai_api_key=None)
            business_dir = answer_eval.prepare_business_dir(case, runtime)
            prompt = answer_eval.acting_prompt(case, runtime, business_dir)
            files = {str(path.relative_to(runtime)) for path in runtime.rglob("*") if path.is_file()}

            self.assertNotIn(case["case_id"], prompt)
            self.assertNotIn(case["source_case_id"], prompt)
            self.assertNotIn("answer_category", prompt)
            self.assertFalse(any(path.startswith("evals/") for path in files))
            self.assertFalse(any("reports/" in path or "runs/" in path for path in files))
            self.assertTrue((runtime / ".codex/skills/money-model-advisor/SKILL.md").exists())
            self.assertTrue((runtime / "reference/corpus_guide_v1.json").exists())

    def test_isolated_codex_home_copies_only_authentication(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            destination = Path(tmp) / "isolated"
            source.mkdir()
            (source / "auth.json").write_text('{"tokens":{"access_token":"abcdefghijklmnopqrstuv"}}\n')
            (source / "AGENTS.md").write_text("global instructions")
            (source / "skills").mkdir()
            (source / "skills" / "SKILL.md").write_text("global skill")

            secrets = answer_eval.prepare_isolated_codex_home(destination, source)

            self.assertEqual({path.name for path in destination.iterdir()}, {"auth.json"})
            self.assertEqual(secrets, ["abcdefghijklmnopqrstuv"])

    def test_audit_packet_binds_answer_and_exact_passages(self):
        case = answer_eval.load_jsonl(CASES_PATH)[0]
        chunk_id = next(iter(answer_eval.CHUNKS))
        session = {
            "assistant_message": f"Supported claim [{chunk_id}]",
            "actions": ["session_start", "search_source_material", "answer"],
            "calculation_events": [],
            "source_events": [{"chunks": [{"id": chunk_id}]}],
            "cited_chunk_ids": [chunk_id],
        }
        packet = answer_eval.audit_packet(case, {"business": {}}, session)
        self.assertEqual(packet["answer_sha256"], answer_eval.sha256_text(session["assistant_message"]))
        self.assertEqual(packet["evidence_passages"][0]["id"], chunk_id)
        self.assertEqual(packet["missing_evidence_chunk_ids"], [])

    def test_session_validation_requires_successful_product_path(self):
        base = {
            "assistant_message": "Answer",
            "metadata": {},
            "source_events": [],
            "calculation_events": [],
            "cited_chunk_ids": [],
        }

        source_case = {"answer_category": "source_grounded"}
        failed_search = dict(base, actions=["session_start", "search_source_material", "answer"])
        self.assertIn("no successful source event", answer_eval.validate_session_for_case(source_case, failed_search))

        valid_source = dict(
            base,
            actions=["session_start", "search_source_material", "answer"],
            source_events=[{"retrieval_backend": "hybrid", "chunks": [{"id": "payback-period:0"}]}],
            cited_chunk_ids=["payback-period:0"],
        )
        self.assertIsNone(answer_eval.validate_session_for_case(source_case, valid_source))

        calculation_case = {"answer_category": "calculation"}
        valid_calculation = dict(
            base,
            actions=["session_start", "calculate", "answer"],
            calculation_events=[{"metric": "payback", "value": 1.0}],
        )
        self.assertIsNone(answer_eval.validate_session_for_case(calculation_case, valid_calculation))

        clarification_case = {"answer_category": "clarification"}
        valid_clarification = dict(base, actions=["session_start", "clarify", "answer"])
        self.assertIsNone(answer_eval.validate_session_for_case(clarification_case, valid_clarification))

    def test_final_semantic_audit_remains_current_and_passing(self):
        audits = answer_scorer.load_jsonl(FINAL_AUDIT_PATH)
        rows, errors = answer_scorer.evaluate_expanded(audits, FINAL_RUNS_PATH)

        self.assertEqual(errors, [])
        self.assertEqual(len(rows), 20)
        self.assertTrue(all(row["current"] for row in rows))
        self.assertTrue(all(row["valid"] for row in rows))
        self.assertTrue(all(row["overall_pass"] for row in rows))
        self.assertEqual(sum(row["claims"] for row in rows), 22)
        self.assertEqual(sum(row["supported_claims"] for row in rows), 22)


if __name__ == "__main__":
    unittest.main()
