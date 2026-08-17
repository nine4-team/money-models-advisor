import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from money_model_architect.advisor_queries import SearchRequest, build_advisor_queries
from money_model_architect.advisor_retrieval import execute_advisor_queries


TRANSCRIPT_DIR = Path(__file__).resolve().parents[1] / "corpus" / "transcripts"


class AdvisorQueryPolicyTest(unittest.TestCase):
    def test_current_search_request_emits_one_unfiltered_query(self):
        search_request = SearchRequest(
            intent="teaching_evidence",
            user_turn="why do we need fulfillment cost?",
            query="fulfillment cost gross profit customer acquisition cost payback",
        )

        queries = build_advisor_queries(search_request)

        self.assertEqual(len(queries), 1)
        self.assertEqual(queries[0].query, search_request.query)
        self.assertEqual(queries[0].subjects, ())
        self.assertEqual(queries[0].target_namespaces, ())

    def test_agent_authored_query_retrieves_local_evidence(self):
        search_request = SearchRequest(
            intent="diagnostic_evidence",
            user_turn="does this mean acquisition is probably not the bottleneck?",
            query="customer acquisition cost first 30 day gross profit payback period",
        )

        evidence = execute_advisor_queries(
            build_advisor_queries(search_request),
            TRANSCRIPT_DIR,
            top_k=3,
        )

        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].intent, "diagnostic_evidence")
        self.assertTrue(evidence[0].chunks)

    def test_distinct_information_needs_preserve_distinct_queries(self):
        teaching = SearchRequest(
            intent="teaching_evidence",
            user_turn="why do we need fulfillment cost?",
            query="gross profit fulfillment cost customer acquisition cost payback period",
        )
        comparison = SearchRequest(
            intent="comparison_evidence",
            user_turn="what is the difference between an attraction offer and an upsell?",
            query="attraction offer versus upsell front end after first sale",
        )

        teaching_query = build_advisor_queries(teaching)[0]
        comparison_query = build_advisor_queries(comparison)[0]

        self.assertNotEqual(teaching_query.query, comparison_query.query)
        self.assertIsNone(teaching_query.subject)
        self.assertIsNone(comparison_query.subject)


if __name__ == "__main__":
    unittest.main()
