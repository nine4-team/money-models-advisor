import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from money_model_architect.advisor import run_single_turn
from money_model_architect.business_context import advisor_paths, sync_business_context
from money_model_architect.snapshot import BusinessSnapshot
from money_model_architect.setup_intake import run_setup


class BusinessSnapshotTest(unittest.TestCase):
    def test_empty_snapshot_shape_and_missing_fields(self):
        snapshot = BusinessSnapshot()
        payload = snapshot.to_dict()

        self.assertEqual(payload["schema_version"], "business_snapshot.v1")
        self.assertIn("money_model", payload)
        self.assertIn("advisor_state", payload)
        self.assertEqual(payload["advisor_state"]["advisory_status"], "insufficient_context")
        self.assertFalse(payload["advisor_state"]["ready_for_payback_diagnosis"])
        self.assertIn("economics.cac", payload["advisor_state"]["missing_fields"])

    def test_payback_readiness_and_derived_payback(self):
        snapshot = BusinessSnapshot()
        snapshot.problem.user_goal = "diagnose cash payback"
        snapshot.business.business_type = "coaching business"
        snapshot.money_model.core_offer.description = "implementation program"
        snapshot.economics.cac = 350
        snapshot.economics.first_30_day_gross_profit = 120
        snapshot.economics.monthly_recurring_gross_profit = 40

        payload = snapshot.to_dict()

        self.assertTrue(payload["advisor_state"]["ready_for_payback_diagnosis"])
        self.assertEqual(payload["advisor_state"]["advisory_status"], "diagnosable")
        self.assertEqual(payload["economics"]["payback_period_months"], 6.75)

    def test_infinite_payback_is_json_null_without_refresh_side_effect_diagnosis(self):
        snapshot = BusinessSnapshot()
        snapshot.problem.user_goal = "diagnose cash payback"
        snapshot.business.business_type = "coaching business"
        snapshot.money_model.core_offer.description = "implementation program"
        snapshot.economics.cac = 350
        snapshot.economics.first_30_day_gross_profit = 120

        payload = snapshot.to_dict()

        self.assertIsNone(payload["economics"]["payback_period_months"])
        self.assertNotIn("payback_not_recovered_without_recurring_gp", payload["problem"]["diagnosed_constraints"])
        self.assertEqual(payload["advisor_state"]["advisory_status"], "diagnosable")

    def test_snapshot_save_load_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "snapshot.json"
            snapshot = BusinessSnapshot()
            snapshot.business.business_type = "agency"
            snapshot.money_model.core_offer.exists = True
            snapshot.money_model.core_offer.description = "done-for-you ads"
            snapshot.save(path)

            loaded = BusinessSnapshot.load(path)

            self.assertEqual(loaded.business.business_type, "agency")
            self.assertTrue(loaded.money_model.core_offer.exists)
            self.assertEqual(loaded.money_model.core_offer.description, "done-for-you ads")


class BusinessContextTest(unittest.TestCase):
    def test_sync_creates_state_and_hash_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            business_dir = Path(tmp)
            (business_dir / "offer.md").write_text("# Offer\nCore offer notes\n", encoding="utf-8")

            manifest, summary = sync_business_context(business_dir)
            paths = advisor_paths(business_dir)

            self.assertTrue(paths.context_manifest.exists())
            self.assertTrue(paths.snapshot.exists())
            self.assertEqual(summary["total"], 1)
            self.assertEqual(summary["changed"], 1)
            self.assertEqual(manifest.files[0].path, "offer.md")

            _, second_summary = sync_business_context(business_dir)
            self.assertEqual(second_summary["unchanged"], 1)
            self.assertEqual(second_summary["changed"], 0)

    def test_single_chat_turn_updates_snapshot_and_persists_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            business_dir = Path(tmp)
            message = (
                "We are a coaching business. Core offer is implementation program. "
                "CAC is $350 and first-30-day gross profit is $120. "
                "I want to diagnose cash payback."
            )

            turn = run_single_turn(business_dir, message)
            paths = advisor_paths(business_dir)
            saved_snapshot = json.loads(paths.snapshot.read_text(encoding="utf-8"))
            sessions = list(paths.sessions_dir.glob("*.json"))

            self.assertIn("payback", turn.assistant_message.lower())
            self.assertEqual(saved_snapshot["business"]["business_type"], "coaching business")
            self.assertEqual(saved_snapshot["economics"]["cac"], 350)
            self.assertEqual(saved_snapshot["economics"]["first_30_day_gross_profit"], 120)
            self.assertTrue(sessions)
            self.assertTrue(turn.evidence)
            self.assertTrue(turn.evidence[0]["chunks"])

    def test_setup_answers_populate_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            business_dir = Path(tmp)
            answers = {
                "business": {
                    "business_type": "coaching business",
                    "icp": "gym owners",
                    "delivery_model": "coaching",
                },
                "money_model": {
                    "core_offer": {"description": "implementation program", "price": 5000},
                    "attraction_offer": {"exists": True},
                    "upsell": {"exists": False},
                    "downsell": {"exists": True},
                    "continuity": {"exists": False},
                },
                "economics": {
                    "cac": 350,
                    "first_30_day_gross_profit": 120,
                    "monthly_recurring_gross_profit": 40,
                },
                "problem": {"user_goal": "diagnose cash payback"},
            }

            snapshot, _summary = run_setup(business_dir, answers=answers)
            saved = json.loads(advisor_paths(business_dir).snapshot.read_text(encoding="utf-8"))

            self.assertTrue(snapshot.advisor_state.ready_for_payback_diagnosis)
            self.assertTrue(saved["advisor_state"]["ready_for_offer_stack_diagnosis"])
            self.assertEqual(saved["advisor_state"]["advisory_status"], "diagnosable")
            self.assertEqual(saved["money_model"]["core_offer"]["price"], 5000)
            self.assertEqual(saved["field_sources"]["business.business_type"]["source_type"], "setup")

    def test_chat_uses_setup_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            business_dir = Path(tmp)
            run_setup(
                business_dir,
                answers={
                    "business.business_type": "coaching business",
                    "business.icp": "gym owners",
                    "money_model.core_offer.description": "implementation program",
                    "money_model.attraction_offer.exists": True,
                    "money_model.upsell.exists": False,
                    "money_model.downsell.exists": True,
                    "money_model.continuity.exists": False,
                    "economics.cac": 350,
                    "economics.first_30_day_gross_profit": 120,
                    "problem.user_goal": "diagnose cash payback",
                },
            )

            turn = run_single_turn(business_dir, "What should I fix first?")

            self.assertIn("payback", turn.assistant_message.lower())
            self.assertNotIn("What is your CAC?", turn.assistant_message)


if __name__ == "__main__":
    unittest.main()
