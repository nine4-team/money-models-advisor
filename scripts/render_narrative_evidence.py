#!/usr/bin/env python3
"""Render human-readable case-level evidence tables into narrative.html.

The narrative keeps aggregate conclusions concise. This renderer derives the
default-closed evidence panels from canonical JSON/JSONL and frozen run
artifacts so the human-facing tables cannot silently diverge from their data.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from collections import defaultdict
from pathlib import Path
from textwrap import indent
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
NARRATIVE = ROOT / "narrative.html"
sys.path.insert(0, str(ROOT / "scripts"))

import eval_calculation_trace_events as calculation_scorer  # noqa: E402
import eval_tool_use_judgment as tool_scorer  # noqa: E402


def read_json(path: str | Path) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (ROOT / path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def fmt_num(value: Any, digits: int = 1) -> str:
    if value is None:
        return "—"
    if isinstance(value, int):
        return f"{value:,}"
    return f"{float(value):,.{digits}f}"


def fmt_ms(value: Any) -> str:
    return "—" if value is None else f"{float(value):,.1f} ms"


def joined(values: Iterable[Any], separator: str = " → ") -> str:
    items = [esc(value) for value in values]
    return separator.join(items) if items else "—"


def status(value: bool, pass_label: str = "Pass", fail_label: str = "Fail") -> str:
    label = pass_label if value else fail_label
    kind = "pass" if value else "fail"
    return f'<span class="evidence-status {kind}">{esc(label)}</span>'


def badge(label: str, kind: str = "neutral") -> str:
    return f'<span class="evidence-status {esc(kind)}">{esc(label)}</span>'


def detail(*sections: tuple[str, str]) -> str:
    body = []
    for label, content in sections:
        body.append(
            f'<div class="evidence-detail-section"><h6>{esc(label)}</h6>{content}</div>'
        )
    return (
        '<details class="evidence-row-detail"><summary>Inspect</summary>'
        f'<div class="evidence-row-body">{"".join(body)}</div></details>'
    )


def para(text: Any) -> str:
    return f"<p>{esc(text)}</p>"


def pre(value: Any) -> str:
    text = value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False)
    return f'<pre class="evidence-answer">{esc(text)}</pre>'


def cell(value: str, sort_value: Any | None = None, css: str = "") -> dict[str, str]:
    return {
        "html": value,
        "sort": str(sort_value if sort_value is not None else html.unescape(value)),
        "class": css,
    }


def evidence_table(
    key: str,
    headers: list[tuple[str, str]],
    rows: list[dict[str, Any]],
    *,
    groups: list[tuple[str, str]] | None = None,
    default_group: str | None = None,
    caption: str,
) -> str:
    toolbar = ['<div class="evidence-toolbar">']
    if groups:
        toolbar.append(f'<label for="filter-{esc(key)}">View</label>')
        toolbar.append(f'<select id="filter-{esc(key)}" class="evidence-filter">')
        for value, label in groups:
            selected = " selected" if value == default_group else ""
            toolbar.append(f'<option value="{esc(value)}"{selected}>{esc(label)}</option>')
        toolbar.append("</select>")
    toolbar.extend(
        [
            f'<label for="search-{esc(key)}">Find a case</label>',
            f'<input id="search-{esc(key)}" class="evidence-search" type="search" placeholder="case, question, result…" />',
            '<span class="evidence-visible-count" aria-live="polite"></span>',
            "</div>",
        ]
    )

    out = [
        '<div class="evidence-dataset">',
        f'<p class="evidence-caption">{esc(caption)}</p>',
        "".join(toolbar),
        '<div class="evidence-table-wrap">',
        f'<table class="evidence-table" data-evidence-table="{esc(key)}">',
        "<thead><tr>",
    ]
    for index, (label, kind) in enumerate(headers):
        out.append(
            f'<th><button type="button" class="evidence-sort" data-column="{index}" '
            f'data-kind="{esc(kind)}">{esc(label)} <span aria-hidden="true">↕</span></button></th>'
        )
    out.extend(["</tr></thead>", "<tbody>"])
    for row in rows:
        classes = " ".join(row.get("classes", []))
        out.append(
            f'<tr data-group="{esc(row.get("group", "all"))}" class="{esc(classes)}">'
        )
        for item in row["cells"]:
            out.append(
                f'<td class="{esc(item.get("class", ""))}" data-sort="{esc(item["sort"])}">'
                f'{item["html"]}</td>'
            )
        out.append("</tr>")
    out.extend(["</tbody></table>", "</div>", "</div>"])
    return "\n".join(out)


def tool_use() -> str:
    cases = read_jsonl("evals/advisor_tool_use_cases.jsonl")
    rows = []
    for case in cases:
        matches = list((ROOT / "evals/runs/next_action").glob(f"*/{case['case_id']}/run.json"))
        if len(matches) != 1:
            raise ValueError(f"expected one tool-use run for {case['case_id']}, found {len(matches)}")
        result = tool_scorer.score_case(case, matches[0])
        passed = result.full_sequence_pass is True
        rows.append(
            {
                "group": case["split"],
                "classes": [] if passed else ["evidence-row-fail"],
                "cells": [
                    cell(f"<code>{esc(case['case_id'])}</code>", case["case_id"]),
                    cell(esc(case["turn_type"]), case["turn_type"]),
                    cell(joined(case["required_actions"]), " ".join(case["required_actions"])),
                    cell(joined(result.actual_actions), " ".join(result.actual_actions)),
                    cell(status(passed), 1 if passed else 0),
                    cell(
                        detail(
                            ("User turn", para(case["user_turn"])),
                            ("Why this label", para(case["label_rationale"])),
                            ("Failures", para(", ".join(result.failure_reasons) or "None")),
                        ),
                        "inspect",
                    ),
                ],
            }
        )
    if len(rows) != 24 or not all("evidence-row-fail" not in row["classes"] for row in rows):
        raise ValueError("tool-use evidence no longer matches the recorded 24/24 result")
    return evidence_table(
        "tool-use",
        [("Case", "text"), ("Turn type", "text"), ("Required", "text"), ("Actual", "text"), ("Result", "number"), ("Details", "text")],
        rows,
        groups=[("all", "All 24 cases"), ("dev", "Development"), ("regression", "Regression"), ("scenario_holdout", "Scenario holdout")],
        default_group="all",
        caption="Every case shows the required action set beside the recorded agent sequence.",
    )


def chunking_pilot() -> str:
    run = read_json("evals/runs/20260604T220451Z-chunking-comparison.json")
    rows = []
    groups = []
    for variant in run["variants"]:
        strategy = variant["strategy"]
        groups.append((strategy, strategy))
        for query in variant["queries"]:
            rows.append(
                {
                    "group": strategy,
                    "classes": [] if query["hit_at_5"] else ["evidence-row-fail"],
                    "cells": [
                        cell(f"<code>{esc(query['id'])}</code>", query["id"]),
                        cell(joined(query["expected_chapters"], ", "), " ".join(query["expected_chapters"])),
                        cell(fmt_num(query["rank"], 0), query["rank"] or 99, "num"),
                        cell(badge("Yes" if query["hit_at_1"] else "No", "pass" if query["hit_at_1"] else "neutral"), int(query["hit_at_1"])),
                        cell(status(query["hit_at_5"], "Yes", "No"), int(query["hit_at_5"])),
                        cell(joined(query["retrieved_chapters"], " · "), " ".join(query["retrieved_chapters"])),
                    ],
                }
            )
    if len(rows) != 160 or len(groups) != 5:
        raise ValueError("unexpected pilot chunking row count")
    return evidence_table(
        "chunking-pilot",
        [("Case", "text"), ("Expected chapter", "text"), ("First hit", "number"), ("Hit@1", "number"), ("Hit@5", "number"), ("Top five chapters", "text")],
        rows,
        groups=[("all", "All strategies"), *groups],
        default_group="framework-aware",
        caption="Choose a strategy to inspect every chapter-level retrieval result.",
    )


def candidate_ids(candidates: list[dict[str, Any]]) -> str:
    values = []
    for candidate in candidates:
        marker = " ✓" if candidate.get("useful") else ""
        values.append(f"{candidate['chunk_id']}{marker}")
    return joined(values, " · ")


def chunking_current() -> str:
    source = read_jsonl("evals/reports/active_query_chunking_revalidation_cases.jsonl")
    order = ["fixed-300", "fixed-512", "fixed-800", "heading-aware", "framework-aware"]
    rows = []
    for row in sorted(source, key=lambda item: (order.index(item["strategy"]), item["case_id"])):
        rank = row["first_useful_rank"]
        rows.append(
            {
                "group": row["strategy"],
                "classes": [] if rank is not None else ["evidence-row-fail"],
                "cells": [
                    cell(f"<code>{esc(row['case_id'])}</code>", row["case_id"]),
                    cell(fmt_num(rank, 0), rank or 99, "num"),
                    cell(f"{row['useful_result_count']} / 5", row["useful_result_count"], "num"),
                    cell(fmt_num(row["returned_word_count"], 0), row["returned_word_count"], "num"),
                    cell(candidate_ids(row["candidates"]), " ".join(c["chunk_id"] for c in row["candidates"])),
                    cell(detail(("User turn", para(row["user_turn"])), ("Saved query", para(row["query"]))), "inspect"),
                ],
            }
        )
    if len(rows) != 230:
        raise ValueError("unexpected current chunking row count")
    return evidence_table(
        "chunking-current",
        [("Case", "text"), ("First useful", "number"), ("Useful", "number"), ("Top-five words", "number"), ("Returned chunks · ✓ useful", "text"), ("Details", "text")],
        rows,
        groups=[("all", "All strategies"), *[(name, name) for name in order]],
        default_group="framework-aware",
        caption="The selected framework-aware condition is shown first; switch strategies without leaving the narrative.",
    )


APPROACH_LABELS = {
    "raw_question": "Raw question",
    "model_rewrite": "Unguided rewrite",
    "guided_model_rewrite_v2": "Corpus-guided rewrite",
}


def retrieval_matrix() -> str:
    source = read_jsonl("evals/reports/active_framework_retrieval_matrix_cases.jsonl")
    rows = []
    groups_seen: dict[str, str] = {}
    for row in source:
        model = row["model"] or "none"
        group = f"{row['approach']}|{model}|{row['retriever']}"
        groups_seen[group] = f"{APPROACH_LABELS[row['approach']]} · {model} · {row['retriever']}"
        rank = row["first_useful_rank"]
        rows.append(
            {
                "group": group,
                "classes": [] if rank is not None else ["evidence-row-fail"],
                "cells": [
                    cell(f"<code>{esc(row['case_id'])}</code>", row["case_id"]),
                    cell(fmt_num(rank, 0), rank or 99, "num"),
                    cell(f"{row['useful_result_count']} / 5", row["useful_result_count"], "num"),
                    cell(fmt_num(row["returned_word_count"], 0), row["returned_word_count"], "num"),
                    cell(candidate_ids(row["candidates"]), " ".join(c["chunk_id"] for c in row["candidates"])),
                    cell(detail(("User turn", para(row["user_turn"])), ("Saved query", para(row["query"]))), "inspect"),
                ],
            }
        )
    if len(rows) != 460 or len(groups_seen) != 10:
        raise ValueError("unexpected retrieval-matrix shape")
    group_order = sorted(groups_seen, key=lambda key: (list(APPROACH_LABELS).index(key.split("|")[0]), key))
    main = evidence_table(
        "retrieval-matrix",
        [("Case", "text"), ("First useful", "number"), ("Useful", "number"), ("Words", "number"), ("Returned chunks · ✓ useful", "text"), ("Details", "text")],
        rows,
        groups=[("all", "All 460 case-condition rows"), *[(key, groups_seen[key]) for key in group_order]],
        default_group="guided_model_rewrite_v2|gpt-5.5|hybrid",
        caption="The selected product condition is the default view. Each row is one frozen query and its five returned chunks.",
    )

    corrections = [
        row
        for row in read_jsonl("evals/active_query_chunking_adjudications.jsonl")
        if row["strategy"] == "framework-aware"
    ]
    correction_rows = []
    for correction in corrections:
        useful = bool(correction["useful"])
        correction_rows.append(
            {
                "cells": [
                    cell(f"<code>{esc(correction['case_id'])}</code>", correction["case_id"]),
                    cell(f"<code>{esc(correction['chunk_id'])}</code>", correction["chunk_id"]),
                    cell(esc(correction["strategy"]), correction["strategy"]),
                    cell(status(useful, "Useful", "Not useful"), int(useful)),
                    cell(esc(correction["rationale"]), correction["rationale"]),
                ]
            }
        )
    if len(corrections) != 13 or sum(bool(row["useful"]) for row in corrections) != 12:
        raise ValueError("label-correction evidence no longer matches 12 additions and one removal")
    audit = evidence_table(
        "retrieval-labels",
        [("Case", "text"), ("Passage", "text"), ("Boundary", "text"), ("Corrected label", "number"), ("Reason", "text")],
        correction_rows,
        caption="Only the 13 labels changed by the audit are shown: 12 additions and one removal.",
    )
    return main + '\n<h5 class="evidence-subhead">Label corrections applied before scoring</h5>\n' + audit


def embedding() -> str:
    source = read_jsonl("evals/reports/embedding_model_comparison_cases.jsonl")
    by_case: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in source:
        by_case[row["case_id"]][row["model"]] = row
    rows = []
    for case_id in sorted(by_case):
        small = by_case[case_id]["text-embedding-3-small"]
        large = by_case[case_id]["text-embedding-3-large-d1536"]
        delta = large["useful_result_count"] - small["useful_result_count"]
        changed = small["returned_chunk_ids"] != large["returned_chunk_ids"]
        rows.append(
            {
                "classes": ["evidence-row-change"] if changed else [],
                "cells": [
                    cell(f"<code>{esc(case_id)}</code>", case_id),
                    cell(fmt_num(small["first_useful_rank"], 0), small["first_useful_rank"] or 99, "num"),
                    cell(f"{small['useful_result_count']} / 5", small["useful_result_count"], "num"),
                    cell(fmt_num(large["first_useful_rank"], 0), large["first_useful_rank"] or 99, "num"),
                    cell(f"{large['useful_result_count']} / 5", large["useful_result_count"], "num"),
                    cell(f"{delta:+d}", delta, "num"),
                    cell("Changed" if changed else "Same", int(changed)),
                    cell(detail(("Small top five", para(" · ".join(small["returned_chunk_ids"]))), ("Large top five", para(" · ".join(large["returned_chunk_ids"])))), "inspect"),
                ],
            }
        )
    if len(source) != 92 or len(rows) != 46:
        raise ValueError("unexpected embedding comparison shape")
    return evidence_table(
        "embedding",
        [("Case", "text"), ("Small rank", "number"), ("Small useful", "number"), ("Large rank", "number"), ("Large useful", "number"), ("Useful Δ", "number"), ("Top five", "number"), ("Details", "text")],
        rows,
        caption="One row compares both embedding models on the same frozen case. Changed rankings are highlighted.",
    )


def latency() -> str:
    original = {
        row["case_id"]: row
        for row in read_jsonl("evals/reports/active_query_pinecone_revalidation_cases.jsonl")
        if row["policy"] == "single"
    }
    optimized = {row["case_id"]: row for row in read_jsonl("evals/reports/pinecone_candidate_depth_optimization_cases.jsonl")}
    large = {row["case_id"]: row for row in read_jsonl("evals/reports/pinecone_large_embedding_revalidation_cases.jsonl")}
    if set(original) != set(optimized) or set(original) != set(large) or len(original) != 46:
        raise ValueError("hosted latency case sets do not align")
    rows = []
    preserved = 0
    for case_id in sorted(original):
        before, after, selected = original[case_id], optimized[case_id], large[case_id]
        same = before["returned_chunk_ids"] == after["returned_chunk_ids"]
        preserved += int(same)
        rows.append(
            {
                "classes": [] if same else ["evidence-row-fail"],
                "cells": [
                    cell(f"<code>{esc(case_id)}</code>", case_id),
                    cell(fmt_ms(before["latency_ms"]), before["latency_ms"], "num"),
                    cell(fmt_ms(after["latency_ms"]), after["latency_ms"], "num"),
                    cell(status(same, "Same", "Changed"), int(same)),
                    cell(fmt_ms(selected["latency_ms"]), selected["latency_ms"], "num"),
                    cell(f"{selected['useful_result_count']} / 5", selected["useful_result_count"], "num"),
                    cell(detail(("Saved query", para(selected["query"])), ("Selected-model top five", para(" · ".join(selected["returned_chunk_ids"])))), "inspect"),
                ],
            }
        )
    if preserved != 46:
        raise ValueError("candidate-depth optimization no longer preserves every top-five list")
    return evidence_table(
        "latency",
        [("Case", "text"), ("250 candidates", "number"), ("25 candidates", "number"), ("Top five", "number"), ("Selected Large", "number"), ("Large useful", "number"), ("Details", "text")],
        rows,
        caption="The first two latency columns isolate candidate-depth optimization; the selected-Large column is the final hosted replay.",
    )


def namespaces() -> str:
    source = read_jsonl("evals/reports/active_query_pinecone_revalidation_cases.jsonl")
    by_case: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in source:
        by_case[row["case_id"]][row["policy"]] = row
    rows = []
    for case_id in sorted(by_case):
        single = by_case[case_id]["single"]
        routed = by_case[case_id]["subject_oracle"]
        changed = single["returned_chunk_ids"] != routed["returned_chunk_ids"]
        rows.append(
            {
                "classes": ["evidence-row-change"] if changed else [],
                "cells": [
                    cell(f"<code>{esc(case_id)}</code>", case_id),
                    cell(fmt_num(single["first_useful_rank"], 0), single["first_useful_rank"] or 99, "num"),
                    cell(f"{single['useful_result_count']} / 5", single["useful_result_count"], "num"),
                    cell(fmt_ms(single["latency_ms"]), single["latency_ms"], "num"),
                    cell(fmt_num(routed["first_useful_rank"], 0), routed["first_useful_rank"] or 99, "num"),
                    cell(f"{routed['useful_result_count']} / 5", routed["useful_result_count"], "num"),
                    cell(fmt_ms(routed["latency_ms"]), routed["latency_ms"], "num"),
                    cell("Changed" if changed else "Same", int(changed)),
                    cell(detail(("Single namespace", para(" · ".join(single["returned_chunk_ids"]))), ("Subject-routed", para(" · ".join(routed["returned_chunk_ids"])))), "inspect"),
                ],
            }
        )
    if len(rows) != 46 or sum("evidence-row-change" in row["classes"] for row in rows) != 9:
        raise ValueError("namespace evidence no longer matches the recorded 37/46 ranking parity")
    note = (
        '<p class="evidence-note">These files preserve the original retrieval lists and latency. '
        'The narrative’s aggregate usefulness percentages use the later label audit; the linked report records that rescore explicitly.</p>'
    )
    return note + evidence_table(
        "namespaces",
        [("Case", "text"), ("Single rank", "number"), ("Single useful*", "number"), ("Single latency", "number"), ("Routed rank", "number"), ("Routed useful*", "number"), ("Routed latency", "number"), ("Ordering", "number"), ("Details", "text")],
        rows,
        caption="Changed top-five orderings are highlighted. The routed condition was given the correct subject.",
    )


def search_decisions() -> str:
    summary = read_json("evals/reports/search_decision_model_comparison_summary.json")
    cases = {row["case_id"]: row for row in read_jsonl("evals/advisor_search_decision_cases.jsonl")}
    rows = []
    for result in sorted(summary["results"], key=lambda row: (row["model"], row["correct"], row["case_id"])):
        case = cases[result["case_id"]]
        passed = bool(result["correct"] and result["valid"])
        rationale = (result.get("response") or {}).get("rationale", "")
        rows.append(
            {
                "group": result["model"],
                "classes": [] if passed else ["evidence-row-fail"],
                "cells": [
                    cell(f"<code>{esc(result['case_id'])}</code>", result["case_id"]),
                    cell(esc(case["scenario_id"]), case["scenario_id"]),
                    cell(esc(case["user_turn"]), case["user_turn"]),
                    cell(esc(result["expected"]), result["expected"]),
                    cell(esc(result["actual"]), result["actual"]),
                    cell(status(passed), int(passed)),
                    cell(fmt_ms(result["latency_ms"]), result["latency_ms"], "num"),
                    cell(detail(("Model rationale", para(rationale)), ("Label rationale", para(case["label_rationale"]))), "inspect"),
                ],
            }
        )
    if len(rows) != 96 or sum("evidence-row-fail" in row["classes"] for row in rows) != 1:
        raise ValueError("search-decision evidence no longer matches 48/48 and 47/48")
    return evidence_table(
        "search-decisions",
        [("Case", "text"), ("Context", "text"), ("Question", "text"), ("Expected", "text"), ("Actual", "text"), ("Result", "number"), ("Latency", "number"), ("Details", "text")],
        rows,
        groups=[("all", "Both models"), ("gpt-5.5", "gpt-5.5"), ("gpt-5.4-mini", "gpt-5.4-mini")],
        default_group="gpt-5.5",
        caption="Filter by model. Failures are highlighted and include both model and answer-key rationales.",
    )


def calculations() -> str:
    cases = read_jsonl("evals/advisor_calculation_trace_cases.jsonl")
    rows = []
    for case in cases:
        run_path = ROOT / "evals/runs/calculation_trace/subagent_v1" / case["case_id"] / "run.json"
        result = calculation_scorer.score_case(case, run_path if run_path.exists() else None)
        passed = result["status"] == "pass"
        expected_metrics = [event["metric"] for event in case["expected_calculation_events"]]
        actual_events = result["actual_calculation_events"]
        actual_summary = ", ".join(f"{event['metric']} = {event['value']}" for event in actual_events) or "No calculation expected"
        rows.append(
            {
                "classes": [] if passed else ["evidence-row-fail"],
                "cells": [
                    cell(f"<code>{esc(case['case_id'])}</code>", case["case_id"]),
                    cell(esc(case["user_turn"]), case["user_turn"]),
                    cell(joined(expected_metrics, ", "), " ".join(expected_metrics)),
                    cell(esc(actual_summary), actual_summary),
                    cell(status(passed), int(passed)),
                    cell(detail(("Expected events", pre(case["expected_calculation_events"])), ("Recorded events", pre(actual_events)), ("Why this label", para(case["label_rationale"]))), "inspect"),
                ],
            }
        )
    if len(rows) != 5 or not all("evidence-row-fail" not in row["classes"] for row in rows):
        raise ValueError("calculation evidence no longer matches 5/5")
    return evidence_table(
        "calculations",
        [("Case", "text"), ("Question", "text"), ("Expected metric", "text"), ("Recorded result", "text"), ("Result", "number"), ("Details", "text")],
        rows,
        caption="Each row compares the expected deterministic event with the event saved in the completed trace.",
    )


def claim_list(claims: list[dict[str, Any]]) -> str:
    if not claims:
        return "<p>No material source-backed claim was scored for this answer.</p>"
    items = []
    for claim in claims:
        verdict = status(bool(claim["supported"]), "Supported", "Unsupported")
        items.append(
            f"<li>{verdict} {esc(claim['claim'])}<span>{esc(claim['rationale'])}</span></li>"
        )
    return f'<ul class="evidence-claims">{"".join(items)}</ul>'


def answer_quality() -> str:
    cases = {row["case_id"]: row for row in read_jsonl("evals/advisor_answer_quality_cases.jsonl")}
    baseline = {row["case_id"]: row for row in read_jsonl("evals/advisor_answer_quality_expanded_baseline_audit.jsonl")}
    final = {row["case_id"]: row for row in read_jsonl("evals/advisor_answer_quality_expanded_final_audit.jsonl")}
    if set(cases) != set(baseline) or set(cases) != set(final) or len(cases) != 20:
        raise ValueError("answer-quality case sets do not align")
    rows = []
    for case_id in sorted(cases, key=lambda cid: (baseline[cid]["overall_pass"], cid)):
        case, before, after = cases[case_id], baseline[case_id], final[case_id]
        before_supported = sum(bool(claim["supported"]) for claim in before["material_claims"])
        after_supported = sum(bool(claim["supported"]) for claim in after["material_claims"])
        baseline_packet = read_json(Path("evals/runs/answer_quality/expanded_v1") / case_id / "audit_packet.json")
        final_packet = read_json(Path("evals/runs/answer_quality/expanded_v1_final") / case_id / "audit_packet.json")
        rows.append(
            {
                "classes": [] if before["overall_pass"] else ["evidence-row-fail"],
                "cells": [
                    cell(f"<code>{esc(case_id)}</code>", case_id),
                    cell(esc(case["scenario_id"]), case["scenario_id"]),
                    cell(esc(case["answer_category"]), case["answer_category"]),
                    cell(status(bool(before["overall_pass"])), int(before["overall_pass"])),
                    cell(f"{before_supported} / {len(before['material_claims'])}", before_supported, "num"),
                    cell(status(bool(after["overall_pass"])), int(after["overall_pass"])),
                    cell(f"{after_supported} / {len(after['material_claims'])}", after_supported, "num"),
                    cell(
                        detail(
                            ("User turn", para(case["user_turn"])),
                            ("Baseline audit", para(before["rationale"]) + claim_list(before["material_claims"])),
                            ("Baseline answer", pre(baseline_packet["assistant_message"])),
                            ("Final audit", para(after["rationale"]) + claim_list(after["material_claims"])),
                            ("Final answer", pre(final_packet["assistant_message"])),
                        ),
                        "inspect",
                    ),
                ],
            }
        )
    baseline_passes = sum(bool(row["overall_pass"]) for row in baseline.values())
    final_passes = sum(bool(row["overall_pass"]) for row in final.values())
    baseline_claims = sum(len(row["material_claims"]) for row in baseline.values())
    baseline_supported = sum(sum(bool(claim["supported"]) for claim in row["material_claims"]) for row in baseline.values())
    final_claims = sum(len(row["material_claims"]) for row in final.values())
    final_supported = sum(sum(bool(claim["supported"]) for claim in row["material_claims"]) for row in final.values())
    if (baseline_passes, final_passes, baseline_supported, baseline_claims, final_supported, final_claims) != (16, 20, 32, 36, 22, 22):
        raise ValueError("answer-quality evidence no longer matches the recorded baseline and final totals")
    return evidence_table(
        "answer-quality",
        [("Case", "text"), ("Context", "text"), ("Category", "text"), ("Baseline", "number"), ("Baseline claims", "number"), ("Final", "number"), ("Final claims", "number"), ("Answers and audit", "text")],
        rows,
        caption="The four baseline failures appear first. Open a row to compare both frozen answers and their claim-level audits.",
    )


RENDERERS = {
    "tool-use": tool_use,
    "chunking-pilot": chunking_pilot,
    "chunking-current": chunking_current,
    "retrieval-matrix": retrieval_matrix,
    "embedding": embedding,
    "latency": latency,
    "namespaces": namespaces,
    "search-decisions": search_decisions,
    "calculations": calculations,
    "answer-quality": answer_quality,
}


def replace_block(document: str, key: str, content: str) -> str:
    start = f"<!-- narrative-evidence:{key}:start -->"
    end = f"<!-- narrative-evidence:{key}:end -->"
    if document.count(start) != 1 or document.count(end) != 1:
        raise ValueError(f"expected exactly one marker pair for {key}")
    before, remainder = document.split(start, 1)
    _, after = remainder.split(end, 1)
    rendered = indent(content, "            ")
    return f"{before}{start}\n{rendered}\n            {end}{after}"


def render(document: str) -> str:
    for key, renderer in RENDERERS.items():
        document = replace_block(document, key, renderer())
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if narrative evidence is stale")
    args = parser.parse_args()
    current = NARRATIVE.read_text(encoding="utf-8")
    rendered = render(current)
    if args.check:
        if rendered != current:
            print("narrative evidence tables are stale; run scripts/render_narrative_evidence.py")
            return 1
        print("narrative evidence tables are current")
        return 0
    NARRATIVE.write_text(rendered, encoding="utf-8")
    print(f"rendered {len(RENDERERS)} evidence tables into {NARRATIVE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
