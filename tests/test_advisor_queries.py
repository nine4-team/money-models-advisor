import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from money_model_architect.advisor_queries import build_advisor_queries
from money_model_architect.advisor_retrieval import execute_advisor_queries
from money_model_architect.snapshot import BusinessSnapshot


TRANSCRIPT_DIR = Path(__file__).resolve().parents[1] / "corpus" / "transcripts"


def diagnosable_snapshot() -> BusinessSnapshot:
    snapshot = BusinessSnapshot()
    snapshot.problem.user_goal = "diagnose cash payback"
    snapshot.business.business_type = "coaching business"
    snapshot.business.icp = "gym owners"
    snapshot.money_model.core_offer.description = "implementation program"
    snapshot.economics.cac = 350
    snapshot.economics.first_30_day_gross_profit = 120
    snapshot.refresh()
    return snapshot


class AdvisorQueryPolicyTest(unittest.TestCase):
    def test_insufficient_context_does_not_query_by_default(self):
        snapshot = BusinessSnapshot()

        queries = build_advisor_queries(snapshot, "What should I fix?")

        self.assertEqual(queries, [])

    def test_diagnosable_snapshot_builds_diagnostic_query(self):
        snapshot = diagnosable_snapshot()

        queries = build_advisor_queries(snapshot)

        self.assertEqual(len(queries), 1)
        self.assertEqual(queries[0].intent, "diagnostic_evidence")
        self.assertEqual(queries[0].layer, "unit-economics")
        self.assertIn("CAC", queries[0].query)
        self.assertIn("payback period", queries[0].query)
        self.assertIn("coaching business", queries[0].query)

    def test_payback_constraint_without_upsell_or_continuity_builds_fix_queries(self):
        snapshot = diagnosable_snapshot()
        snapshot.problem.diagnosed_constraints.append("payback_not_recovered_without_recurring_gp")
        snapshot.money_model.attraction_offer.exists = True
        snapshot.money_model.upsell.exists = False
        snapshot.money_model.downsell.exists = True
        snapshot.money_model.continuity.exists = False
        snapshot.refresh()

        queries = build_advisor_queries(snapshot)

        self.assertEqual([query.layer for query in queries], ["upsells", "continuity"])
        self.assertTrue(all(query.intent == "recommendation_evidence" for query in queries))
        self.assertIn("upsell after first sale", queries[0].query)
        self.assertIn("continuity recurring gross profit", queries[1].query)

    def test_framework_comparison_builds_one_query_per_framework(self):
        snapshot = BusinessSnapshot()

        queries = build_advisor_queries(snapshot, "Compare rollover upsell and classic upsell")

        self.assertEqual(len(queries), 2)
        self.assertTrue(all(query.intent == "framework_comparison" for query in queries))
        self.assertEqual([query.query for query in queries], ["rollover upsell", "classic upsell"])

    def test_diagnostic_query_retrieves_local_evidence(self):
        snapshot = diagnosable_snapshot()
        queries = build_advisor_queries(snapshot)

        evidence = execute_advisor_queries(queries, TRANSCRIPT_DIR, top_k=3)

        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].intent, "diagnostic_evidence")
        self.assertTrue(evidence[0].chunks)
        self.assertTrue(all("unit-economics" in chunk.layers for chunk in evidence[0].chunks))

    def test_recommendation_queries_retrieve_local_evidence(self):
        snapshot = diagnosable_snapshot()
        snapshot.problem.diagnosed_constraints.append("payback_not_recovered_without_recurring_gp")
        snapshot.money_model.attraction_offer.exists = True
        snapshot.money_model.upsell.exists = False
        snapshot.money_model.downsell.exists = True
        snapshot.money_model.continuity.exists = False
        snapshot.refresh()
        queries = build_advisor_queries(snapshot)

        evidence = execute_advisor_queries(queries, TRANSCRIPT_DIR, top_k=2)

        self.assertEqual([item.layer for item in evidence], ["upsells", "continuity"])
        self.assertTrue(all(item.chunks for item in evidence))


if __name__ == "__main__":
    unittest.main()
