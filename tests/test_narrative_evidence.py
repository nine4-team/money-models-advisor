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


if __name__ == "__main__":
    unittest.main()
