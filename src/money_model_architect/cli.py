"""Command-line entry point for the local proof harness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .advisor import run_single_turn
from .business_context import advisor_paths, ensure_advisor_state
from .calculator import (
    UnitEconomics,
    cac,
    cfa_level,
    gross_margin,
    gross_profit,
    lifetime_gross_profit,
    payback_period_months,
)
from .diagnose import diagnose
from .retrieval import CorpusIndex
from .setup_intake import load_answers, run_setup


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Money Model Architect local proof harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search transcript chunks")
    search.add_argument("query")
    search.add_argument("--layer", choices=("unit-economics", "offers", "upsells", "downsells", "continuity"))
    search.add_argument("--top-k", type=int, default=5)

    calc = subparsers.add_parser("calculate", help="Run deterministic unit-economics formulas")
    calc.add_argument("metric", choices=("cac", "gross-profit", "gross-margin", "ltgp", "payback", "cfa-level"))
    calc.add_argument("--inputs", required=True, help="JSON object with metric inputs")

    diag = subparsers.add_parser("diagnose", help="Diagnose the active money-model constraint")
    diag.add_argument("--snapshot", required=True, help="JSON business snapshot")

    setup = subparsers.add_parser("setup", help="Initialize advisor state for a business directory")
    setup.add_argument("--business-dir", required=True, help="Directory for local business context and advisor state")
    setup.add_argument("--answers", help="JSON object or path to JSON file with setup answers")
    setup.add_argument("--interactive", action="store_true", help="Prompt for missing setup fields")

    sync = subparsers.add_parser("sync", help="Alias for setup")
    sync.add_argument("--business-dir", required=True, help="Directory containing local business context")

    chat = subparsers.add_parser("chat", help="Run the first stateful advisor chat loop")
    chat.add_argument("--business-dir", required=True, help="Directory containing advisor state")
    chat.add_argument("--message", help="Single user message. If omitted, starts a simple interactive loop.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "search":
        index = CorpusIndex.from_transcripts(_repo_root() / "corpus" / "transcripts")
        results = index.search(args.query, layer=args.layer, top_k=args.top_k)
        payload = [
            {
                "id": result.chunk.id,
                "chapter": result.chunk.chapter,
                "layer": result.chunk.layer,
                "layers": list(result.chunk.layers),
                "score": round(result.score, 3),
                "preview": result.chunk.text[:260].replace("\n", " "),
            }
            for result in results
        ]
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "calculate":
        inputs = json.loads(args.inputs)
        metric = args.metric
        if metric == "cac":
            value = cac(inputs["total_acquisition_cost"], inputs["new_customers"])
        elif metric == "gross-profit":
            value = gross_profit(inputs["price"], inputs["cogs"])
        elif metric == "gross-margin":
            value = gross_margin(inputs["price"], inputs["cogs"])
        elif metric == "ltgp":
            value = lifetime_gross_profit(inputs["monthly_price"], inputs["monthly_churn_rate"], inputs["gross_margin"])
        elif metric == "payback":
            value = payback_period_months(inputs["cac"], inputs["month_one_gp"], inputs["monthly_recurring_gp"])
        else:
            value = cfa_level(inputs["cac"], inputs["first_30_day_gp"])
        print(json.dumps({"metric": metric, "value": value}, indent=2))
        return 0

    if args.command in {"setup", "sync"}:
        answers = load_answers(args.answers) if getattr(args, "answers", None) else None
        snapshot, summary = run_setup(
            Path(args.business_dir),
            answers=answers,
            interactive=getattr(args, "interactive", False),
        )
        paths = advisor_paths(Path(args.business_dir))
        payload = {
            "business_dir": str(paths.business_dir),
            "state_dir": str(paths.state_dir),
            "manifest": str(paths.context_manifest),
            "snapshot": str(paths.snapshot),
            "summary": summary,
            "advisory_status": snapshot.advisor_state.advisory_status,
            "ready_for_payback_diagnosis": snapshot.advisor_state.ready_for_payback_diagnosis,
            "ready_for_offer_stack_diagnosis": snapshot.advisor_state.ready_for_offer_stack_diagnosis,
            "missing_fields": snapshot.advisor_state.missing_fields,
        }
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "chat":
        business_dir = Path(args.business_dir)
        paths = advisor_paths(business_dir)
        ensure_advisor_state(paths)
        if args.message:
            turn = run_single_turn(business_dir, args.message)
            print(turn.assistant_message)
            return 0

        print("Money Model Advisor. Type 'exit' to quit.")
        while True:
            try:
                message = input("> ").strip()
            except EOFError:
                break
            if message.lower() in {"exit", "quit"}:
                break
            if not message:
                continue
            turn = run_single_turn(business_dir, message)
            print(turn.assistant_message)
        return 0

    snapshot = json.loads(args.snapshot)
    economics = UnitEconomics(
        cac=snapshot["cac"],
        first_30_day_gross_profit=snapshot.get("first_30_day_gross_profit", 0.0),
        monthly_recurring_gross_profit=snapshot.get("monthly_recurring_gross_profit", 0.0),
        lifetime_gross_profit=snapshot.get("lifetime_gross_profit"),
        gross_margin=snapshot.get("gross_margin"),
        service_business=snapshot.get("service_business", False),
    )
    print(json.dumps(diagnose(economics).to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
