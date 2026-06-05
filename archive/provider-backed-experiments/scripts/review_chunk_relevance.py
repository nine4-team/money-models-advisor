#!/usr/bin/env python3
"""Serve a local UI for blind query/chunk relevance judgments."""

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

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9-]*")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
STOPWORDS = {
    "a",
    "about",
    "and",
    "are",
    "but",
    "can",
    "for",
    "from",
    "how",
    "if",
    "is",
    "it",
    "of",
    "or",
    "should",
    "that",
    "the",
    "them",
    "they",
    "this",
    "to",
    "what",
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


def inferred_query_phrases(query: str, text: str, limit: int = 2) -> list[str]:
    query_tokens = token_set(query)
    if not query_tokens:
        return []
    scored = []
    for sentence in SENTENCE_RE.split(text):
        sentence = sentence.strip()
        if len(sentence) < 32:
            continue
        sentence_tokens = token_set(sentence)
        overlap = query_tokens & sentence_tokens
        if not overlap:
            continue
        score = len(overlap) / max(1, len(query_tokens))
        scored.append((score, len(overlap), sentence))
    scored.sort(reverse=True, key=lambda item: (item[0], item[1]))
    return [sentence for _score, _overlap, sentence in scored[:limit]]


def highlighted_text(text: str, phrases: list[str]) -> str:
    escaped = html.escape(text)
    for phrase in sorted((phrase for phrase in phrases if phrase.strip()), key=len, reverse=True):
        escaped_phrase = html.escape(phrase)
        escaped = escaped.replace(escaped_phrase, f"<mark>{escaped_phrase}</mark>")
    return escaped


def status_counts(rows: list[dict]) -> dict[str, int]:
    counts = {"unreviewed": 0, "0": 0, "1": 0, "2": 0}
    for row in rows:
        relevance = row.get("relevance")
        if relevance is None:
            counts["unreviewed"] += 1
        else:
            counts[str(relevance)] = counts.get(str(relevance), 0) + 1
    return counts


def render_page(pool_path: Path) -> bytes:
    rows = load_jsonl(pool_path)
    chunks = chunk_lookup()
    counts = status_counts(rows)

    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(row["query_id"], []).append(row)

    sections = []
    for query_id, items in groups.items():
        first = items[0]
        cards = []
        reviewed = sum(1 for item in items if item.get("relevance") is not None)
        for item in items:
            relevance = item.get("relevance")
            status = "unreviewed" if relevance is None else f"rel-{relevance}"
            text = chunks.get(item["chunk_id"], "[missing chunk]")
            phrases = inferred_query_phrases(item["query"], text)
            cards.append(
                f"""
                <article class="card {html.escape(status)}">
                  <div class="meta">Review ID: {html.escape(item['id'])}</div>
                  <div class="chunk-title">Candidate chunk: {html.escape(item['chunk_id'])}</div>
                  <pre>{highlighted_text(text, phrases)}</pre>
                  <form method="POST" action="/review">
                    <input type="hidden" name="id" value="{html.escape(item['id'])}">
                    <textarea name="notes" placeholder="Optional note">{html.escape(item.get('notes', ''))}</textarea>
                    <button name="relevance" value="2">2 Useful</button>
                    <button name="relevance" value="1">1 Partial</button>
                    <button name="relevance" value="0">0 Not Useful</button>
                    <button name="relevance" value="">Clear</button>
                  </form>
                </article>
                """
            )
        hint = ", ".join(first.get("candidate_chapters", []))
        sections.append(
            f"""
            <section class="query-group">
              <div class="label">Query Type: {html.escape(first.get('query_type', 'unknown'))}</div>
              <h2>{html.escape(first['query'])}</h2>
              <p class="hint">Reviewer orientation: layer hint <strong>{html.escape(str(first.get('target_layer_hint')))}</strong>; candidate chapters <strong>{html.escape(hint)}</strong>. Retriever source is hidden.</p>
              <p class="progress">{reviewed} of {len(items)} chunks reviewed for this query</p>
              {''.join(cards)}
            </section>
            """
        )

    body = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Chunk Relevance Review</title>
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #202124; background: #f8f9fb; }}
        header, .query-group {{ max-width: 1040px; margin: 0 auto 28px; }}
        .summary {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }}
        .pill {{ background: #e8edf5; border: 1px solid #d3dbe8; border-radius: 999px; padding: 6px 10px; font-size: 13px; }}
        .query-group {{ border-top: 1px solid #d7dce2; padding-top: 22px; }}
        .card {{ margin: 12px 0 18px; background: white; border: 1px solid #d7dce2; border-radius: 8px; padding: 18px; }}
        .unreviewed {{ border-left: 6px solid #7b8794; }}
        .rel-0 {{ border-left: 6px solid #a42d2d; }}
        .rel-1 {{ border-left: 6px solid #9a6a00; }}
        .rel-2 {{ border-left: 6px solid #16833a; }}
        .meta, .hint, .progress {{ color: #5f6876; font-size: 13px; }}
        .label {{ color: #5f6876; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0; margin-bottom: 4px; }}
        .chunk-title {{ font-weight: 700; margin-bottom: 8px; }}
        h1 {{ margin-bottom: 4px; }}
        h2 {{ margin: 0 0 8px; font-size: 24px; }}
        pre {{ white-space: pre-wrap; background: #f1f4f8; border: 1px solid #dde3ea; padding: 12px; border-radius: 6px; line-height: 1.45; }}
        mark {{ background: #fff2a8; border: 1px solid #ead16b; border-radius: 3px; padding: 0 2px; }}
        textarea {{ display: block; width: 100%; min-height: 52px; margin: 12px 0; }}
        button {{ margin-right: 8px; padding: 8px 12px; }}
      </style>
    </head>
    <body>
      <header>
        <h1>Chunk Relevance Review</h1>
        <p>Judge whether each chunk is useful evidence for the query. Retriever source is hidden during review.</p>
        <div class="summary">
          <span class="pill">Unreviewed: {counts['unreviewed']}</span>
          <span class="pill">2 Useful: {counts.get('2', 0)}</span>
          <span class="pill">1 Partial: {counts.get('1', 0)}</span>
          <span class="pill">0 Not Useful: {counts.get('0', 0)}</span>
        </div>
      </header>
      {''.join(sections) or '<p>No chunk relevance rows found.</p>'}
      <script>
        window.addEventListener('load', () => {{
          const y = sessionStorage.getItem('chunkRelevanceReviewScrollY');
          if (y !== null) {{
            window.scrollTo(0, Number(y));
            sessionStorage.removeItem('chunkRelevanceReviewScrollY');
          }}
        }});
        document.addEventListener('submit', () => {{
          sessionStorage.setItem('chunkRelevanceReviewScrollY', String(window.scrollY));
        }});
      </script>
    </body>
    </html>
    """
    return body.encode("utf-8")


def make_handler(pool_path: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if urlparse(self.path).path != "/":
                self.send_error(404)
                return
            content = render_page(pool_path)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self) -> None:
            if urlparse(self.path).path != "/review":
                self.send_error(404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            data = parse_qs(self.rfile.read(length).decode("utf-8"))
            target_id = data.get("id", [""])[0]
            relevance_raw = data.get("relevance", [""])[0]
            notes = data.get("notes", [""])[0]
            rows = load_jsonl(pool_path)
            for row in rows:
                if row.get("id") == target_id:
                    row["relevance"] = None if relevance_raw == "" else int(relevance_raw)
                    row["status"] = "unreviewed" if relevance_raw == "" else "reviewed"
                    row["notes"] = notes
                    break
            write_jsonl(pool_path, rows)
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

        def log_message(self, format: str, *args) -> None:
            return

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description="Review chunk relevance labels")
    parser.add_argument("--pool", type=Path, default=ROOT / "evals" / "chunk_relevance_pool.jsonl")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), make_handler(args.pool))
    print(f"Chunk relevance review UI: http://{args.host}:{args.port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
