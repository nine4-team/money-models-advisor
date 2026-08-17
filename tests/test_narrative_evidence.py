import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import render_narrative_evidence as evidence  # noqa: E402


class EvidenceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.evidence_panels = 0
        self.evidence_tables = 0
        self.iframes = 0
        self.open_evidence_panels = 0
        self.workflow_nodes = set()
        self.workflow_edges = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if tag == "details" and "evidence-data" in classes:
            self.evidence_panels += 1
            self.open_evidence_panels += int("open" in attrs)
        if tag == "table" and "evidence-table" in classes:
            self.evidence_tables += 1
        if tag == "iframe":
            self.iframes += 1
        if "data-node" in attrs:
            self.workflow_nodes.add(attrs["data-node"])
        if "data-from" in attrs and "data-to" in attrs:
            self.workflow_edges.add((attrs["data-from"], attrs["data-to"]))


class NarrativeEvidenceTest(unittest.TestCase):
    def test_generated_evidence_is_current(self):
        document = evidence.NARRATIVE.read_text(encoding="utf-8")
        self.assertEqual(evidence.render(document), document)

    def test_evidence_is_human_readable_and_closed_by_default(self):
        parser = EvidenceParser()
        parser.feed(evidence.NARRATIVE.read_text(encoding="utf-8"))

        self.assertEqual(parser.evidence_panels, 10)
        self.assertEqual(parser.open_evidence_panels, 0)
        self.assertEqual(parser.evidence_tables, 11)
        self.assertEqual(parser.iframes, 0)

    def test_clarification_ends_the_workflow_turn(self):
        parser = EvidenceParser()
        parser.feed(evidence.NARRATIVE.read_text(encoding="utf-8"))

        self.assertIn("clarify", parser.workflow_nodes)
        self.assertFalse(any(source == "clarify" for source, _ in parser.workflow_edges))
        for action in ("inspect", "calculate", "search"):
            self.assertIn((action, "action-complete"), parser.workflow_edges)
        self.assertIn(("action-complete", "enough-context"), parser.workflow_edges)


if __name__ == "__main__":
    unittest.main()
