import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from eval_advisor_answer_quality import evaluate


class AdvisorAnswerQualityEvalTest(unittest.TestCase):
    def test_answer_hash_prevents_stale_semantic_judgment(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp)
            run_dir = runs / "case_1"
            run_dir.mkdir()
            answer = "Current answer"
            (run_dir / "run.json").write_text(
                json.dumps({"assistant_message": answer}), encoding="utf-8"
            )
            audit = {
                "case_id": "case_1",
                "answer_sha256": hashlib.sha256("Old answer".encode()).hexdigest(),
                "recommendation_correct": True,
                "recommendation_useful": True,
                "claims": [],
            }

            rows = evaluate([audit], runs)

            self.assertFalse(rows[0]["current"])

    def test_supported_claims_are_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp)
            run_dir = runs / "case_1"
            run_dir.mkdir()
            answer = "Current answer"
            (run_dir / "run.json").write_text(
                json.dumps({"assistant_message": answer}), encoding="utf-8"
            )
            audit = {
                "case_id": "case_1",
                "answer_sha256": hashlib.sha256(answer.encode()).hexdigest(),
                "recommendation_correct": True,
                "recommendation_useful": True,
                "claims": [{"supported": True}, {"supported": False}],
            }

            rows = evaluate([audit], runs)

            self.assertTrue(rows[0]["current"])
            self.assertEqual(rows[0]["supported_claims"], 1)
            self.assertEqual(rows[0]["claims"], 2)


if __name__ == "__main__":
    unittest.main()
