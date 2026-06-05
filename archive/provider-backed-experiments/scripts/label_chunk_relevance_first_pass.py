#!/usr/bin/env python3
"""Create AI-assisted first-pass labels for the chunk relevance pool."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from money_model_architect.env import load_env_file  # noqa: E402
from money_model_architect.retrieval import CorpusIndex  # noqa: E402

OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def chunk_lookup() -> dict[str, str]:
    index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking="heading-aware")
    return {chunk.id: chunk.text for chunk in index.chunks}


def call_openai(api_key: str, model: str, messages: list[dict[str, str]]) -> tuple[dict[str, Any], dict[str, int]]:
    body = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 4000,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        OPENAI_CHAT_COMPLETIONS_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI relevance-label request failed: {exc.code} {detail}") from exc

    content = payload["choices"][0]["message"]["content"]
    usage = payload.get("usage", {})
    return json.loads(content), {
        "prompt_tokens": int(usage.get("prompt_tokens", 0)),
        "completion_tokens": int(usage.get("completion_tokens", 0)),
        "total_tokens": int(usage.get("total_tokens", 0)),
    }


def prompt_for_group(query_rows: list[dict[str, Any]], chunks: dict[str, str]) -> list[dict[str, str]]:
    first = query_rows[0]
    chunk_payload = [
        {
            "id": row["id"],
            "chunk_id": row["chunk_id"],
            "chunk_chapter": row.get("chunk_chapter"),
            "text": chunks.get(row["chunk_id"], ""),
        }
        for row in query_rows
    ]
    system = (
        "You are a careful RAG relevance judge. Label each candidate chunk for whether it is useful evidence "
        "for answering the user's query. Do not reward a chunk just because it shares vocabulary with the query. "
        "Pay close attention to timing, scope, and whether the chunk supports the actual decision the user asked about. "
        "A chunk can be useful evidence even if it does not answer every part of the query. "
        "Return only valid JSON."
    )
    user = {
        "query_id": first["query_id"],
        "query": first["query"],
        "query_type": first.get("query_type"),
        "orientation_hints_not_labels": {
            "target_layer_hint": first.get("target_layer_hint"),
            "candidate_chapters": first.get("candidate_chapters", []),
        },
        "rubric": {
            "2": "Directly useful, cite-worthy evidence for answering an important part of this query.",
            "1": "Partially useful or background context, but not strong enough to cite as main support.",
            "0": "Not useful evidence for this query.",
        },
        "output_contract": {
            "required_ids": [row["id"] for row in query_rows],
            "instruction": "Return exactly one label for every required id and no prose outside JSON.",
            "labels": [
                {
                    "id": "row id from input",
                    "relevance": "0, 1, or 2",
                    "confidence": "low, medium, or high",
                    "notes": "one concise reason grounded in the query and chunk",
                }
            ]
        },
        "chunks": chunk_payload,
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
    ]


def label_rows(rows: list[dict[str, Any]], model: str, overwrite: bool, pool_path: Path) -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for AI-assisted first-pass relevance labels")

    chunks = chunk_lookup()
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if overwrite or row.get("relevance") is None:
            groups[row["query_id"]].append(row)

    usage_totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    labeled = 0
    reviewed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    reviewer = f"openai_first_pass:{model}"

    for group_index, (query_id, query_rows) in enumerate(groups.items(), start=1):
        if not query_rows:
            continue
        print(f"[{group_index}/{len(groups)}] labeling {query_id} ({len(query_rows)} rows)", flush=True)
        labels_by_id = {}
        missing = [row["id"] for row in query_rows]
        for attempt in range(1, 4):
            payload, usage = call_openai(api_key, model, prompt_for_group(query_rows, chunks))
            for key in usage_totals:
                usage_totals[key] += usage[key]
            labels_by_id = {label["id"]: label for label in payload.get("labels", [])}
            missing = [row["id"] for row in query_rows if row["id"] not in labels_by_id]
            if not missing:
                break
            time.sleep(attempt)
        if missing:
            raise RuntimeError(f"Model response omitted labels for {query_id} after retries: {missing}")

        for row in query_rows:
            label = labels_by_id[row["id"]]
            relevance = int(label["relevance"])
            if relevance not in {0, 1, 2}:
                raise RuntimeError(f"Invalid relevance for {row['id']}: {label['relevance']}")
            if row.get("relevance") is not None and overwrite:
                row.setdefault("previous_review", {
                    "relevance": row.get("relevance"),
                    "reviewer": row.get("reviewer"),
                    "notes": row.get("notes", ""),
                })
            row["relevance"] = relevance
            row["status"] = "reviewed"
            row["reviewer"] = reviewer
            row["reviewed_at"] = reviewed_at
            row["confidence"] = str(label.get("confidence", "medium")).lower()
            row["notes"] = str(label.get("notes", "")).strip()
            labeled += 1
        write_jsonl(pool_path, rows)
        print(f"[{group_index}/{len(groups)}] saved {query_id}", flush=True)

    return {
        "reviewer": reviewer,
        "groups_labeled": len(groups),
        "rows_labeled": labeled,
        "usage": usage_totals,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create AI-assisted first-pass chunk relevance labels")
    parser.add_argument("--pool", type=Path, default=ROOT / "evals" / "chunk_relevance_pool.jsonl")
    parser.add_argument("--model", default=os.environ.get("OPENAI_RELEVANCE_MODEL", "gpt-4o-mini"))
    parser.add_argument("--overwrite", action="store_true", help="Replace existing relevance labels")
    args = parser.parse_args()

    load_env_file(ROOT / ".env.local")
    load_env_file(ROOT / ".env")

    rows = load_jsonl(args.pool)
    run = label_rows(rows, args.model, args.overwrite, args.pool)
    write_jsonl(args.pool, rows)
    print(json.dumps(run, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
