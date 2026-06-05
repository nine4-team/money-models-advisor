#!/usr/bin/env python3
"""Serve a tiny local UI for reviewing obligation-to-chunk labels."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from money_model_architect.retrieval import CorpusIndex  # noqa: E402

SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9-]*")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "for",
    "from",
    "how",
    "if",
    "in",
    "is",
    "it",
    "of",
    "or",
    "should",
    "that",
    "the",
    "their",
    "then",
    "they",
    "this",
    "to",
    "when",
    "with",
}


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def chunk_lookup() -> dict[str, str]:
    index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking="heading-aware")
    return {chunk.id: chunk.text for chunk in index.chunks}


def token_set(text: str) -> set[str]:
    return {token for token in TOKEN_RE.findall(text.lower()) if token not in STOPWORDS and len(token) > 2}


def inferred_support_phrases(claim: str, text: str, limit: int = 2) -> list[str]:
    claim_tokens = token_set(claim)
    if not claim_tokens:
        return []
    scored = []
    for sentence in SENTENCE_RE.split(text):
        sentence = sentence.strip()
        if len(sentence) < 24:
            continue
        sentence_tokens = token_set(sentence)
        overlap = claim_tokens & sentence_tokens
        if not overlap:
            continue
        score = len(overlap) / max(1, len(claim_tokens))
        scored.append((score, len(overlap), sentence))
    scored.sort(reverse=True, key=lambda item: (item[0], item[1]))
    return [sentence for _score, _overlap, sentence in scored[:limit]]


def highlighted_text(text: str, phrases: list[str]) -> str:
    escaped = html.escape(text)
    for phrase in sorted((phrase for phrase in phrases if phrase.strip()), key=len, reverse=True):
        escaped_phrase = html.escape(phrase)
        escaped = escaped.replace(escaped_phrase, f"<mark>{escaped_phrase}</mark>")
    return escaped


def render_page(obligations_path: Path) -> bytes:
    obligations = [row for row in load_jsonl(obligations_path) if row.get("id") != "placeholder"]
    chunks = chunk_lookup()
    groups: dict[str, list[dict]] = {}
    for item in obligations:
        groups.setdefault(item.get("query", ""), []).append(item)

    sections = []
    for query, items in groups.items():
        cards = []
        for item in items:
            status = item.get("status", "proposed")
            chunk_ids = item.get("supporting_chunk_ids", [])
            supporting_phrases = item.get("supporting_phrases", [])
            chunk_html = []
            for chunk_id in chunk_ids:
                text = chunks.get(chunk_id, "[missing chunk]")
                phrases = supporting_phrases or inferred_support_phrases(item["claim"], text)
                phrase_note = "curated" if supporting_phrases else "auto"
                chunk_html.append(
                    f"""
                    <h4>Proposed supporting chunk: {html.escape(chunk_id)} <span class="highlight-mode">{phrase_note} highlights</span></h4>
                    <pre>{highlighted_text(text, phrases)}</pre>
                    """
                )
            cards.append(
                f"""
                <article class="card {html.escape(status)}">
                  <div class="meta">{html.escape(item['id'])} · {html.escape(status)}</div>
                  <div class="label">Required supported claim</div>
                  <h3>{html.escape(item['claim'])}</h3>
                  {''.join(chunk_html)}
                  <form method="POST" action="/review">
                    <input type="hidden" name="id" value="{html.escape(item['id'])}">
                    <textarea name="notes" placeholder="Review notes">{html.escape(item.get('notes', ''))}</textarea>
                    <button name="status" value="accepted">Yes</button>
                    <button name="status" value="rejected">No</button>
                    <button name="status" value="needs_better_chunk">Needs Better Chunk</button>
                    <button name="status" value="proposed">Clear Selection</button>
                  </form>
                </article>
                """
            )
        sections.append(
            f"""
            <section class="query-group">
              <div class="label">Eval query</div>
              <h2>{html.escape(query)}</h2>
              <p class="group-help">Review each required claim separately. These claims are eval labels only: they are not shown to the answer generator.</p>
              {''.join(cards)}
            </section>
            """
        )
    body = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Required Claim Review</title>
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #202124; background: #f8f9fb; }}
        header {{ max-width: 980px; margin: 0 auto 24px; }}
        .query-group {{ max-width: 980px; margin: 0 auto 28px; }}
        .card {{ margin: 12px 0 18px; background: white; border: 1px solid #d7dce2; border-radius: 8px; padding: 18px; }}
        .accepted {{ border-left: 6px solid #16833a; }}
        .rejected {{ border-left: 6px solid #a42d2d; }}
        .needs_better_chunk {{ border-left: 6px solid #9a6a00; }}
        .proposed {{ border-left: 6px solid #4e6bd8; }}
        .meta {{ color: #5f6876; font-size: 13px; margin-bottom: 8px; }}
        .label {{ color: #5f6876; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0; margin-bottom: 4px; }}
        h1 {{ margin-bottom: 4px; }}
        h2 {{ margin: 0 0 6px; font-size: 24px; }}
        h3 {{ margin: 0 0 8px; }}
        h4 {{ margin: 16px 0 6px; }}
        .group-help {{ color: #3f4855; margin: 0 0 12px; }}
        pre {{ white-space: pre-wrap; background: #f1f4f8; border: 1px solid #dde3ea; padding: 12px; border-radius: 6px; line-height: 1.45; }}
        mark {{ background: #fff2a8; border: 1px solid #ead16b; border-radius: 3px; padding: 0 2px; }}
        .highlight-mode {{ color: #667085; font-size: 12px; font-weight: 500; margin-left: 6px; }}
        textarea {{ display: block; width: 100%; min-height: 54px; margin: 12px 0; }}
        button {{ margin-right: 8px; padding: 8px 12px; }}
      </style>
    </head>
    <body>
      <header>
        <h1>Required Claim Review</h1>
        <p>Approve only when the chunk directly supports the required claim. Yellow highlights are proposed support spans to help you scan faster; still judge the full chunk when needed.</p>
      </header>
      {''.join(sections) or '<p>No required-claim labels found.</p>'}
      <script>
        window.addEventListener('load', () => {{
          const y = sessionStorage.getItem('requiredClaimReviewScrollY');
          if (y !== null) {{
            window.scrollTo(0, Number(y));
            sessionStorage.removeItem('requiredClaimReviewScrollY');
          }}
        }});
        document.addEventListener('submit', () => {{
          sessionStorage.setItem('requiredClaimReviewScrollY', String(window.scrollY));
        }});
      </script>
    </body>
    </html>
    """
    return body.encode("utf-8")


def make_handler(obligations_path: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/":
                self.send_error(404)
                return
            content = render_page(obligations_path)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/review":
                self.send_error(404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            data = parse_qs(self.rfile.read(length).decode("utf-8"))
            target_id = data.get("id", [""])[0]
            status = data.get("status", ["proposed"])[0]
            notes = data.get("notes", [""])[0]
            rows = load_jsonl(obligations_path)
            for row in rows:
                if row.get("id") == target_id:
                    row["status"] = status
                    row["notes"] = notes
                    break
            write_jsonl(obligations_path, rows)
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

        def log_message(self, format: str, *args) -> None:
            return

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description="Review required supported claim labels")
    parser.add_argument("--obligations", type=Path, default=ROOT / "evals" / "obligations.jsonl")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), make_handler(args.obligations))
    print(f"Review UI: http://{args.host}:{args.port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
