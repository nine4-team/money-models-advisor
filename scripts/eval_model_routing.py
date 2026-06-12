#!/usr/bin/env python3
"""Model-routing/tiering eval over the existing golden suites.

This is the explicit model/provider comparison experiment allowed by
`JD_REQUIREMENTS_AUDIT.md` and `AGENTS.md`: the same golden cases are replayed
as single bounded completions against multiple hosted model tiers, then scored
with the existing deterministic scorers (`eval_source_need_generation.py` and
`eval_tool_use_judgment.py`). It does not replace the acting-agent product
path, and it is not hidden model use: every raw response is recorded as a run
artifact under `evals/runs/model_routing/`.

Two suites are replayed because their model task is one bounded JSON
completion with an existing validator:

- source_need: decide search/no-search and emit a structured SourceNeed.
- tool_use: emit the ordered next-action sequence from the fixed taxonomy.

The recorded interactive acting-agent traces (Claude via CLI sessions) are
scored with the same scorers and reported as a reference condition. That
condition ran with CLI access and multi-step state inspection, so it is a
different harness: quality is comparable in direction only, and latency/cost
are not comparable at all.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import capture_source_need_trace as sn_capture  # noqa: E402
import eval_source_need_generation as sn_eval  # noqa: E402
import eval_tool_use_judgment as tu_eval  # noqa: E402
from money_model_architect.embeddings import load_env_file  # noqa: E402

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

# Static pricing table, USD per 1M tokens, recorded June 2026. Reasoning
# tokens are billed as completion tokens, so completion_tokens covers them.
PRICING_PER_1M = {
    "gpt-5": (1.25, 10.00),
    "gpt-5-mini": (0.25, 2.00),
    "gpt-5-nano": (0.05, 0.40),
    "gpt-4.1-mini": (0.40, 1.60),
}

DEFAULT_MODELS = ("gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-4.1-mini")
RETRYABLE_HTTP = {429, 500, 502, 503, 504}

SOURCE_NEED_OUTPUT_INSTRUCTIONS = """All business state is provided inline below; you cannot run CLI commands in this harness.

Respond with only one JSON object and no prose, in this shape:

{"source_search_decision": true, "source_need": {"intent": "...", "layers": ["..."], "focus_terms": ["..."]}}

or, when source search is not needed:

{"source_search_decision": false, "source_need": null}"""

TOOL_USE_TAXONOMY_INSTRUCTIONS = """You are the acting agent for a Money Model Advisor next-action eval case. Decide the ordered sequence of actions you would take for the current user turn before answering. All business state is provided inline below; you cannot run CLI commands in this harness, so report the actions you would take.

Action taxonomy (use these exact strings):

- `clarify`: ask the user for a missing fact that blocks a responsible answer.
- `update_snapshot`: persist a new business fact the user just provided.
- `read_snapshot`: read saved business economics and offer-stack state.
- `read_logs`: read prior-session records for earlier conversation context.
- `inspect_local_docs`: read the business's own local documents.
- `calculate`: run a deterministic metric calculation (CAC, gross profit, payback, CFA level).
- `diagnose`: run the deterministic money-model diagnosis over saved state.
- `search_source_material`: search the Money Models source corpus for citeable support.
- `compose_answer_from_state`: compose the answer from saved state and tool outputs.
- `answer_without_tool`: answer directly when no state or source support is needed.

Rules:

- Report only the actions this turn needs. Extra actions count against you.
- Do not use source-material search as a substitute for missing business facts.
- Do not search the source corpus for simple vocabulary answers.
- Each action needs `confidence`: `direct` when the provided state directly supports taking it, otherwise `inferred`.
- For tool-like actions (`update_snapshot`, `read_snapshot`, `read_logs`, `inspect_local_docs`, `calculate`, `diagnose`, `search_source_material`) with `direct` confidence, include `evidence_type` (one of `snapshot_field`, `session_file`, `local_doc`, `user_turn`, `planned_cli`) and `evidence_ref` naming the concrete field, file, or command you would rely on.

Respond with only one JSON object and no prose, in this shape:

{"actions": [{"action": "read_snapshot", "confidence": "direct", "evidence_type": "snapshot_field", "evidence_ref": "economics.cac"}, {"action": "compose_answer_from_state", "confidence": "inferred"}]}"""


def utc_now() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fixture_text(rel: str | None) -> str | None:
    if not rel:
        return None
    return (ROOT / rel).read_text(encoding="utf-8").strip()


def local_docs_block(rel: str | None) -> str:
    if not rel:
        return "- none"
    docs_dir = ROOT / rel
    parts: list[str] = []
    for doc in sorted(docs_dir.glob("*")):
        if doc.is_file():
            parts.append(f"### {doc.name}\n\n{doc.read_text(encoding='utf-8').strip()}")
    return "\n\n".join(parts) if parts else "- none"


def state_blocks(case: dict[str, Any], include_local_docs: bool) -> str:
    blocks = [
        "Business snapshot (saved state):",
        "",
        "```json",
        fixture_text(case.get("snapshot_fixture_path")) or "null",
        "```",
        "",
        "Prior session records:",
        "",
    ]
    sessions = fixture_text(case.get("prior_sessions_fixture_path"))
    if sessions:
        blocks.extend(["```json", sessions, "```"])
    else:
        blocks.append("- none")
    if include_local_docs:
        blocks.extend(["", "Local business documents:", "", local_docs_block(case.get("local_docs_fixture_path"))])
    return "\n".join(blocks)


def source_need_prompt(case: dict[str, Any]) -> str:
    base = sn_capture.render_acting_prompt(case, Path("(inline-state)"))
    # Keep the capture prompt's decision policy verbatim; strip only the
    # interactive-harness lines that do not apply to a bounded completion.
    harness_markers = (
        "Use the money-model-advisor skill and local CLI",
        "Business dir:",
        "After acting, complete the trace",
    )
    lines = [line for line in base.splitlines() if not any(marker in line for marker in harness_markers)]
    if len(lines) == len(base.splitlines()):
        raise SystemExit("source-need capture prompt changed shape; update eval_model_routing.py harness markers")
    return "\n".join(
        [
            "\n".join(lines).strip(),
            "",
            state_blocks(case, include_local_docs=False),
            "",
            SOURCE_NEED_OUTPUT_INSTRUCTIONS,
        ]
    )


def tool_use_prompt(case: dict[str, Any]) -> str:
    hidden = {
        "split",
        "turn_type",
        "snapshot_fixture_path",
        "local_docs_fixture_path",
        "prior_sessions_fixture_path",
        "required_actions",
        "allowed_actions",
        "forbidden_actions",
        "expected_first_action",
        "search_allowed",
        "expected_mutation",
        "label_rationale",
        "ambiguity",
        "severity_if_wrong",
    }
    visible_case = {key: value for key, value in case.items() if key not in hidden and not key.startswith("_")}
    return "\n".join(
        [
            "# Next-Action Eval Acting Prompt",
            "",
            TOOL_USE_TAXONOMY_INSTRUCTIONS,
            "",
            "Visible case context:",
            "",
            "```json",
            json.dumps(visible_case, indent=2, sort_keys=True),
            "```",
            "",
            state_blocks(case, include_local_docs=True),
        ]
    )


class ChatError(RuntimeError):
    pass


def call_chat(model: str, prompt: str, api_key: str, timeout: float, max_completion_tokens: int) -> dict[str, Any]:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "max_completion_tokens": max_completion_tokens,
    }
    last_error: Exception | None = None
    for attempt in range(4):
        started = time.perf_counter()
        request = urllib.request.Request(
            OPENAI_CHAT_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            latency_ms = (time.perf_counter() - started) * 1000
            usage = payload.get("usage", {})
            content = payload["choices"][0]["message"]["content"]
            return {
                "content": content,
                "latency_ms": round(latency_ms, 1),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "attempts": attempt + 1,
            }
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            last_error = ChatError(f"HTTP {exc.code}: {detail[:500]}")
            if exc.code not in RETRYABLE_HTTP:
                break
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError) as exc:
            last_error = ChatError(f"{type(exc).__name__}: {exc}")
        time.sleep(2**attempt)
    raise ChatError(f"chat request failed for {model}: {last_error}")


def estimated_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    input_rate, output_rate = PRICING_PER_1M[model]
    return (prompt_tokens * input_rate + completion_tokens * output_rate) / 1_000_000


def parse_model_json(content: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(content)
    except json.JSONDecodeError as exc:
        return None, f"json_decode_error: {exc}"
    if not isinstance(value, dict):
        return None, "response_not_object"
    return value, None


def run_payload_for_suite(suite: str, case: dict[str, Any], parsed: dict[str, Any] | None, parse_error: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {"case_id": case["case_id"]}
    if suite == "source_need":
        if parsed is not None:
            decision = parsed.get("source_search_decision")
            payload["source_search_decision"] = decision if isinstance(decision, bool) else None
            payload["source_need"] = parsed.get("source_need")
        else:
            payload["source_search_decision"] = None
            payload["source_need"] = None
    else:
        actions = parsed.get("actions") if parsed is not None else None
        payload["actual_actions"] = actions if isinstance(actions, list) else []
    if parse_error:
        payload["parse_error"] = parse_error
    return payload


def run_case(
    suite: str,
    case: dict[str, Any],
    model: str,
    runs_dir: Path,
    api_key: str,
    timeout: float,
    max_completion_tokens: int,
    force: bool,
) -> Path:
    run_dir = runs_dir / model / suite / case["case_id"]
    run_path = run_dir / "run.json"
    if run_path.exists() and not force:
        return run_path

    prompt = source_need_prompt(case) if suite == "source_need" else tool_use_prompt(case)
    meta: dict[str, Any] = {"model": model, "suite": suite, "created_at": utc_now(), "sampling": "provider defaults"}
    try:
        response = call_chat(model, prompt, api_key, timeout, max_completion_tokens)
        parsed, parse_error = parse_model_json(response["content"])
        meta.update(
            {
                "latency_ms": response["latency_ms"],
                "prompt_tokens": response["prompt_tokens"],
                "completion_tokens": response["completion_tokens"],
                "attempts": response["attempts"],
                "estimated_cost_usd": round(estimated_cost(model, response["prompt_tokens"], response["completion_tokens"]), 8),
                "raw_content": response["content"],
            }
        )
    except ChatError as exc:
        parsed, parse_error = None, f"request_failed: {exc}"
        meta["request_error"] = str(exc)

    payload = run_payload_for_suite(suite, case, parsed, parse_error)
    payload["model_meta"] = meta
    (run_dir / "prompt.md").parent.mkdir(parents=True, exist_ok=True)
    (run_dir / "prompt.md").write_text(prompt, encoding="utf-8")
    write_json(run_path, payload)
    return run_path


def score_source_need(cases: list[dict[str, Any]], artifacts: dict[str, Path]) -> dict[str, Any]:
    results = [sn_eval.score_case(case, artifacts.get(case["case_id"])) for case in cases]
    scored = [result for result in results if result.status != "not_run"]
    search_expected = [result for result in scored if result.expected_search]
    # The base scorer's failure_reasons cover trace issues only; derive quality
    # misses per case so the failure-mode section reflects wrong judgments too.
    case_failures: dict[str, list[str]] = {}
    for result in scored:
        reasons = list(result.failure_reasons)
        if result.missed_search:
            reasons.append("missed_search")
        if result.false_search:
            reasons.append("false_search")
        if result.expected_search and result.actual_search:
            if result.intent_match is False:
                reasons.append("intent_mismatch")
            if result.layer_exact_match is False:
                reasons.append("layer_mismatch")
        if reasons:
            case_failures[result.case_id] = reasons
    failures = Counter(reason for reasons in case_failures.values() for reason in reasons)
    strict_pass = sum(
        1
        for result in scored
        if result.actual_search == result.expected_search
        and (not result.expected_search or (result.intent_match is True and result.layer_exact_match is True))
    )
    return {
        "results": results,
        "scored": len(scored),
        "total": len(cases),
        "strict_case_pass_rate": strict_pass / len(scored) if scored else None,
        "search_decision_accuracy": sum(result.actual_search == result.expected_search for result in scored) / len(scored) if scored else None,
        "intent_match_rate": sum(result.intent_match is True for result in search_expected) / len(search_expected) if search_expected else None,
        "layer_exact_match_rate": sum(result.layer_exact_match is True for result in search_expected) / len(search_expected) if search_expected else None,
        "avg_focus_recall": sn_eval.avg([result.focus_recall for result in search_expected]),
        "failure_modes": dict(failures.most_common()),
        "case_failures": case_failures,
    }


def score_tool_use(cases: list[dict[str, Any]], artifacts: dict[str, Path]) -> dict[str, Any]:
    results = [tu_eval.score_case(case, artifacts.get(case["case_id"])) for case in cases]
    scored = [result for result in results if result.status == "scored"]
    case_failures = {result.case_id: list(result.failure_reasons) for result in scored if result.failure_reasons}
    failures = Counter(reason for reasons in case_failures.values() for reason in reasons)
    recalls = [result.required_recall for result in scored if result.required_recall is not None]
    return {
        "results": results,
        "scored": len(scored),
        "total": len(cases),
        "strict_case_pass_rate": sum(result.full_sequence_pass is True for result in scored) / len(scored) if scored else None,
        "first_action_accuracy": sum(result.first_action_correct is True for result in scored) / len(scored) if scored else None,
        "avg_required_recall": sum(recalls) / len(recalls) if recalls else None,
        "forbidden_violation_rate": sum(result.forbidden_violation is True for result in scored) / len(scored) if scored else None,
        "false_search_rate": sum(result.false_search is True for result in scored) / len(scored) if scored else None,
        "missed_search_rate": sum(result.missed_search is True for result in scored) / len(scored) if scored else None,
        "failure_modes": dict(failures.most_common()),
        "case_failures": case_failures,
    }


SUITES = {
    "source_need": {
        "cases_path": ROOT / "evals" / "advisor_source_need_cases.jsonl",
        "loader": sn_eval.load_jsonl,
        "scorer": score_source_need,
        "find_artifacts": sn_eval.find_run_artifacts,
        "recorded_runs_dir": ROOT / "evals" / "runs" / "source_need" / "taxonomy_v2",
    },
    "tool_use": {
        "cases_path": ROOT / "evals" / "advisor_tool_use_cases.jsonl",
        "loader": tu_eval.load_jsonl,
        "scorer": score_tool_use,
        "find_artifacts": tu_eval.find_run_artifacts,
        "recorded_runs_dir": ROOT / "evals" / "runs" / "next_action",
    },
}


def perf_summary(model: str, run_paths: list[Path]) -> dict[str, Any]:
    latencies: list[float] = []
    prompt_tokens = 0
    completion_tokens = 0
    request_errors = 0
    for path in run_paths:
        meta = json.loads(path.read_text(encoding="utf-8")).get("model_meta", {})
        if "request_error" in meta:
            request_errors += 1
            continue
        latencies.append(meta.get("latency_ms", 0.0))
        prompt_tokens += meta.get("prompt_tokens", 0)
        completion_tokens += meta.get("completion_tokens", 0)
    cost = estimated_cost(model, prompt_tokens, completion_tokens)
    return {
        "requests": len(run_paths),
        "request_errors": request_errors,
        "p50_latency_ms": round(statistics.median(latencies), 1) if latencies else None,
        "p95_latency_ms": round(statistics.quantiles(latencies, n=20)[18], 1) if len(latencies) >= 2 else (round(latencies[0], 1) if latencies else None),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "estimated_cost_usd": round(cost, 6),
        "estimated_cost_per_case_usd": round(cost / len(latencies), 6) if latencies else None,
    }


def fmt_pct(value: float | None) -> str:
    return "-" if value is None else f"{value * 100:.1f}%"


def fmt_num(value: float | None, digits: int = 3) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def render_report(models: list[str], suites: list[str], quality: dict[str, dict[str, dict[str, Any]]], perf: dict[str, dict[str, dict[str, Any]]], recorded: dict[str, dict[str, Any]]) -> str:
    lines = [
        "# Model Routing And Tiering Eval",
        "",
        "## Scope",
        "",
        "This experiment replays two golden suites as single bounded JSON completions across hosted model tiers, then scores every condition with the existing deterministic scorers. The suites are `source_need` (search/no-search decision plus structured SourceNeed) and `tool_use` (ordered next-action sequence from the fixed taxonomy). These two were chosen because the model task is one validated completion, so the comparison isolates model judgment from harness differences.",
        "",
        "This is the explicit model-comparison experiment allowed by `JD_REQUIREMENTS_AUDIT.md`. Raw prompts and responses are recorded under `evals/runs/model_routing/` for audit. Sampling uses provider defaults; gpt-5-family models run with default reasoning effort, which is part of what the latency column measures.",
        "",
        "The recorded interactive acting-agent condition (Claude operating the CLI in captured trace sessions) is scored with the same scorers as a reference row. It had CLI access, real state inspection, and multi-step iteration, so treat its quality as a different-harness reference, not a same-task competitor; its latency and cost are not comparable and are omitted.",
        "",
        "## Quality",
        "",
        "Strict case pass means: search/no-search decision correct, and on expected-search cases intent match plus exact layer match (`source_need`); or required-action recall 1.0 with no forbidden actions and a complete trace (`tool_use`).",
        "",
    ]

    def source_need_row(label: str, q: dict[str, Any]) -> str:
        return (
            f"| {label} | {fmt_pct(q['strict_case_pass_rate'])} | {fmt_pct(q['search_decision_accuracy'])} | "
            f"{fmt_pct(q['intent_match_rate'])} | {fmt_pct(q['layer_exact_match_rate'])} | {fmt_num(q['avg_focus_recall'])} |"
        )

    def tool_use_row(label: str, q: dict[str, Any]) -> str:
        return (
            f"| {label} | {fmt_pct(q['strict_case_pass_rate'])} | {fmt_pct(q['first_action_accuracy'])} | "
            f"{fmt_num(q['avg_required_recall'])} | {fmt_pct(q['forbidden_violation_rate'])} | "
            f"{fmt_pct(q['false_search_rate'])} | {fmt_pct(q['missed_search_rate'])} |"
        )

    suite_tables = {
        "source_need": (
            "| Condition | Strict Case Pass | Search Decision | Intent Match | Layer Exact | Focus Concept Recall |",
            "|---|---:|---:|---:|---:|---:|",
            source_need_row,
        ),
        "tool_use": (
            "| Condition | Strict Case Pass | First Action | Required Recall | Forbidden Violations | False Search | Missed Search |",
            "|---|---:|---:|---:|---:|---:|---:|",
            tool_use_row,
        ),
    }
    for suite in suites:
        header, divider, row = suite_tables[suite]
        case_count = quality[models[0]][suite]["total"]
        lines.extend([f"### {suite} ({case_count} cases)", "", header, divider])
        for model in models:
            lines.append(row(f"`{model}`", quality[model][suite]))
        lines.append(row("recorded acting agent (reference)", recorded[suite]))
        lines.append("")

    lines.extend(
        [
            "",
            "## Latency And Cost",
            "",
            "Latency is wall-clock per completion including provider queue and default reasoning. Cost uses the static June 2026 pricing table in `scripts/eval_model_routing.py`; reasoning tokens bill as completion tokens.",
            "",
            "| Model | Suite | p50 Latency | p95 Latency | Prompt Tokens | Completion Tokens | Est. Cost | Est. Cost / Case | Request Errors |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for model in models:
        for suite in suites:
            p = perf[model][suite]
            per_case = p["estimated_cost_per_case_usd"]
            per_case_text = "-" if per_case is None else f"${per_case:.6f}"
            lines.append(
                f"| `{model}` | `{suite}` | {fmt_num(p['p50_latency_ms'], 0)} ms | {fmt_num(p['p95_latency_ms'], 0)} ms | "
                f"{p['prompt_tokens']} | {p['completion_tokens']} | ${p['estimated_cost_usd']:.4f} | "
                f"{per_case_text} | {p['request_errors']} |"
            )

    lines.extend(["", "## Failure Modes", ""])
    for model in models:
        for suite in suites:
            modes = quality[model][suite]["failure_modes"]
            rendered = ", ".join(f"`{name}` x{count}" for name, count in modes.items()) if modes else "none"
            lines.append(f"- `{model}` / `{suite}`: {rendered}")
    for suite in suites:
        modes = recorded[suite]["failure_modes"]
        rendered = ", ".join(f"`{name}` x{count}" for name, count in modes.items()) if modes else "none"
        lines.append(f"- recorded acting agent / `{suite}`: {rendered}")

    lines.extend(
        [
            "",
            "## Interpretation And Routing Decision",
            "",
            "This section interprets the June 2026 full-matrix run (4 OpenAI tiers x 38 cases, 0 request errors). Re-running with different models or cases requires re-authoring it.",
            "",
            "1. **No cheaper tier maintains output quality on agent-planning tasks, so nothing routes downward in v1.** The strongest tier tested (`gpt-5`) reaches 71.4% strict pass on `source_need` versus 92.9% for the recorded interactive agent, and every cheaper tier is materially worse. The JD asks for routing that improves unit economics *while maintaining output quality*; on these suites that bar is not met by any tested downgrade, and recording that is the routing decision.",
            "",
            "2. **Tier separation is real and directional on `source_need`.** `gpt-5` holds 100% search-decision accuracy. The cheaper reasoning tiers fail closed: `gpt-5-mini` misses 5 of 10 expected searches and `gpt-5-nano` misses 9 of 10, declining clearly search-worthy turns. The non-reasoning `gpt-4.1-mini` fails open instead: 3 false searches on the 4 no-search controls. Failing closed degrades answer citations silently; failing open burns retrieval cost and pollutes answers. Neither failure direction is acceptable as a default.",
            "",
            "3. **Model family changes the failure mode, not just the rate.** The gpt-5 reasoning family never violated the output contract; `gpt-4.1-mini` returned malformed action objects on 3 of 24 `tool_use` cases on top of the highest wrong-first-action rate. It is also roughly 10x faster (p50 about 1.0-1.2s versus 5-14s) and 20x cheaper per case than `gpt-5` — a real latency/cost win that the quality column disqualifies for planning tasks, but which would matter for bounded low-stakes transforms.",
            "",
            "4. **Cheap-tier reasoning is not free.** `gpt-5-nano` spent 45,599 completion tokens on `tool_use` — more than triple `gpt-5-mini` — for equal-or-worse quality. Token-based pricing keeps it cheapest in dollars, but its p50 latency (about 9-14s) lands near `gpt-5`. Routing decisions should be made on the measured latency/quality pair, not the price sheet alone.",
            "",
            "5. **Caveat: the `tool_use` replay is harness-coupled.** Six cases fail across every API tier while the recorded interactive agent passed all of them. Those labels require CLI actions (`read_snapshot`, `calculate`, `search_source_material`) that a bounded completion with state already inlined tends to skip in favor of answering directly. Part of the API-tier gap on `tool_use` therefore measures harness mismatch, not model judgment; `source_need` is the cleaner tier discriminator. The recorded-agent comparison also crosses providers (Claude interactive versus OpenAI bounded), so it is direction-of-evidence, not a controlled provider benchmark.",
            "",
            "Routing policy for v1: deterministic work (calculation, diagnosis, retrieval execution, trace recording) stays in the CLI at zero model cost — that is the product's primary unit-economics lever. Agent planning (next action, source need) stays on the strong interactive tier. The first candidates for routed downgrades are bounded low-stakes transforms such as query-variant phrasing, and any downgrade must first match the recorded baseline on the relevant golden suite.",
            "",
            "## Per-Case Failures",
            "",
            "| Model | Suite | Case | Failure Reasons |",
            "|---|---|---|---|",
        ]
    )
    any_failure = False
    for model in models:
        for suite in suites:
            for case_id, reasons in quality[model][suite]["case_failures"].items():
                any_failure = True
                lines.append(f"| `{model}` | `{suite}` | `{case_id}` | {', '.join(reasons)} |")
    if not any_failure:
        lines.append("| - | - | - | none |")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", default=list(DEFAULT_MODELS), choices=sorted(PRICING_PER_1M))
    parser.add_argument("--suites", nargs="+", default=list(SUITES), choices=sorted(SUITES))
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "evals" / "runs" / "model_routing")
    parser.add_argument("--report", type=Path, default=ROOT / "evals" / "reports" / "model_routing_tiering.md")
    parser.add_argument("--summary-json", type=Path, default=ROOT / "evals" / "reports" / "model_routing_tiering_summary.json")
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--max-completion-tokens", type=int, default=6000)
    parser.add_argument("--force", action="store_true", help="Re-run completions even when run.json artifacts exist.")
    args = parser.parse_args()

    load_env_file(ROOT / ".env")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required (environment or repo .env)")

    suite_cases = {suite: SUITES[suite]["loader"](SUITES[suite]["cases_path"]) for suite in args.suites}

    jobs = [(suite, case, model) for suite in args.suites for case in suite_cases[suite] for model in args.models]
    with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        futures = {
            pool.submit(
                run_case, suite, case, model, args.runs_dir, api_key, args.timeout, args.max_completion_tokens, args.force
            ): (suite, case["case_id"], model)
            for suite, case, model in jobs
        }
        for future, (suite, case_id, model) in futures.items():
            future.result()
            print(f"done {model} {suite} {case_id}", file=sys.stderr)

    quality: dict[str, dict[str, dict[str, Any]]] = {}
    perf: dict[str, dict[str, dict[str, Any]]] = {}
    for model in args.models:
        quality[model] = {}
        perf[model] = {}
        for suite in args.suites:
            suite_dir = args.runs_dir / model / suite
            artifacts = SUITES[suite]["find_artifacts"](suite_dir)
            quality[model][suite] = SUITES[suite]["scorer"](suite_cases[suite], artifacts)
            perf[model][suite] = perf_summary(model, sorted(suite_dir.rglob("run.json")))

    recorded: dict[str, dict[str, Any]] = {}
    for suite in args.suites:
        artifacts = SUITES[suite]["find_artifacts"](SUITES[suite]["recorded_runs_dir"])
        recorded[suite] = SUITES[suite]["scorer"](suite_cases[suite], artifacts)

    report = render_report(args.models, args.suites, quality, perf, recorded)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")

    def strip_results(block: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in block.items() if key not in ("results", "case_failures")}

    summary = {
        "created_at": utc_now(),
        "models": args.models,
        "suites": args.suites,
        "pricing_per_1m_usd": {model: PRICING_PER_1M[model] for model in args.models},
        "quality": {model: {suite: strip_results(quality[model][suite]) for suite in args.suites} for model in args.models},
        "performance": perf,
        "recorded_acting_agent_reference": {suite: strip_results(recorded[suite]) for suite in args.suites},
    }
    write_json(args.summary_json, summary)
    print(json.dumps({"report": rel_path(args.report), "summary": rel_path(args.summary_json)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
