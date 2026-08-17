#!/usr/bin/env python3
"""Generate frozen full answers through sanitized Money Model Advisor runtimes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "evals" / "advisor_answer_quality_cases.jsonl"
DEFAULT_RUNS = ROOT / "evals" / "runs" / "answer_quality" / "expanded_v1"
RUNTIME_FILES = ("pyproject.toml",)
RUNTIME_TREES = ("src", "corpus")
EMBEDDING_CACHE = Path(".cache/embeddings/openai/text-embedding-3-large-d1536")


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_cases(cases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    ids = [case.get("case_id") for case in cases]
    if len(ids) != len(set(ids)):
        errors.append("case_id values must be unique")
    allowed_categories = {"source_grounded", "calculation", "clarification"}
    for case in cases:
        case_id = case.get("case_id", "<missing>")
        if case.get("answer_category") not in allowed_categories:
            errors.append(f"{case_id}: invalid answer_category")
        if not case.get("user_turn"):
            errors.append(f"{case_id}: missing user_turn")
        fixture = case.get("snapshot_fixture_path")
        if not fixture or not (ROOT / fixture).exists():
            errors.append(f"{case_id}: missing snapshot fixture")
        for optional_fixture in ("local_docs_fixture_path", "prior_sessions_fixture_path"):
            value = case.get(optional_fixture)
            if value and not (ROOT / value).exists():
                errors.append(f"{case_id}: missing {optional_fixture}")
    return errors


def _dotenv_value(name: str) -> str | None:
    env_value = os.getenv(name)
    if env_value:
        return env_value
    env_path = ROOT / ".env"
    if not env_path.exists():
        return None
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == name:
            return value.strip().strip("'\"")
    return None


def _copy_tree(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def prepare_isolated_codex_home(destination: Path, source_home: Path | None = None) -> list[str]:
    """Copy only CLI authentication, excluding global skills, plugins, and task state."""
    source_home = source_home or (Path.home() / ".codex")
    destination.mkdir(parents=True, exist_ok=True)
    auth_source = source_home / "auth.json"
    if not auth_source.exists():
        raise FileNotFoundError(f"Codex authentication file not found: {auth_source}")
    auth_target = destination / "auth.json"
    shutil.copy2(auth_source, auth_target)
    auth_target.chmod(0o600)

    payload = json.loads(auth_source.read_text(encoding="utf-8"))
    sensitive_values: list[str] = []

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)
        elif isinstance(value, str) and len(value) >= 20:
            sensitive_values.append(value)

    collect(payload)
    return sensitive_values


def copy_runtime(destination: Path, openai_api_key: str | None) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for relative in RUNTIME_FILES:
        shutil.copy2(ROOT / relative, destination / relative)
    for relative in RUNTIME_TREES:
        _copy_tree(ROOT / relative, destination / relative)

    skill_source = ROOT / ".codex" / "skills" / "money-model-advisor"
    skill_target = destination / ".codex" / "skills" / "money-model-advisor"
    skill_target.mkdir(parents=True, exist_ok=True)
    for filename in ("SKILL.md", "search_request_rules.md"):
        text = (skill_source / filename).read_text(encoding="utf-8")
        text = text.replace(str(ROOT), str(destination))
        text = text.replace(
            "../../../evals/query_generation/corpus_guide_v1.json",
            "../../../reference/corpus_guide_v1.json",
        )
        (skill_target / filename).write_text(text, encoding="utf-8")

    reference_dir = destination / "reference"
    reference_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        ROOT / "evals" / "query_generation" / "corpus_guide_v1.json",
        reference_dir / "corpus_guide_v1.json",
    )

    source_cache = ROOT / EMBEDDING_CACHE
    if source_cache.exists():
        target_cache = destination / EMBEDDING_CACHE
        target_cache.parent.mkdir(parents=True, exist_ok=True)
        _copy_tree(source_cache, target_cache)

    if openai_api_key:
        env_path = destination / ".env"
        env_path.write_text(f"OPENAI_API_KEY={openai_api_key}\n", encoding="utf-8")
        env_path.chmod(0o600)

    (destination / "AGENTS.md").write_text(
        "# Money Model Advisor Runtime\n\n"
        "Use the local money-model-advisor skill. The human talks to the agent; "
        "the CLI performs deterministic state, calculation, retrieval, and trace "
        "work. Do not inspect `.env`, `.cache`, or paths outside this runtime. "
        "There are no evaluation labels or prior trial outputs here.\n",
        encoding="utf-8",
    )


def _copy_session_fixture(source: Path, sessions_dir: Path) -> None:
    payload = json.loads(source.read_text(encoding="utf-8"))
    turns = payload.get("turns")
    if isinstance(turns, list):
        for index, turn in enumerate(turns, 1):
            write_json(
                sessions_dir / f"prior_{index:02d}.json",
                {
                    "created_at": turn.get("timestamp"),
                    "user_message": turn.get("user_message"),
                    "assistant_message": turn.get("assistant_message"),
                    "actions": turn.get("actions", []),
                    "retrieval_queries": turn.get("retrieval_queries", []),
                    "evidence": turn.get("evidence", []),
                },
            )
    else:
        shutil.copy2(source, sessions_dir / source.name)


def prepare_business_dir(case: dict[str, Any], runtime: Path) -> Path:
    business_dir = runtime / "business"
    state_dir = business_dir / ".money-model-advisor"
    sessions_dir = state_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / case["snapshot_fixture_path"], state_dir / "business_snapshot.json")

    local_docs = case.get("local_docs_fixture_path")
    if local_docs:
        source = ROOT / local_docs
        if source.is_dir():
            shutil.copytree(source, business_dir, dirs_exist_ok=True)
        else:
            shutil.copy2(source, business_dir / source.name)

    prior_sessions = case.get("prior_sessions_fixture_path")
    if prior_sessions:
        _copy_session_fixture(ROOT / prior_sessions, sessions_dir)
    return business_dir


def acting_prompt(case: dict[str, Any], runtime: Path, business_dir: Path) -> str:
    return f"""# Money Model Advisor Turn

Act as the Money Model Advisor and answer the user's request through the normal
skill-guided workflow.

1. Read and follow the local `money-model-advisor` skill and its search-request rules.
2. Use the CLI from `{runtime}` with `{business_dir}` as the business directory.
3. Start the turn with `session start`. Decide naturally whether to calculate,
   search the local Money Models corpus, clarify, or answer from saved context.
4. If you search, use the current single-query `SearchRequest` and the default
   hybrid retriever. Inspect the returned passages, cite only supported claims, and
   preserve the CLI's `retrieval_backend` field in the recorded source event.
5. Record the complete turn with `session finish` before returning. Keep the
   `actions` list exhaustive; if the answer asks for missing decision-critical
   information, include `clarify`.
6. Work only inside `{runtime}`. Do not inspect `.env`, `.cache`, or any path
   outside this runtime. No evaluation labels or previous trials are available.
7. Return only the user-facing answer recorded in the completed session.

User request:

{case['user_turn']}
"""


def codex_command(model: str, runtime: Path, output_path: Path) -> list[str]:
    return [
        "codex",
        "--ask-for-approval",
        "never",
        "exec",
        "--ephemeral",
        "--model",
        model,
        "--cd",
        str(runtime),
        "--sandbox",
        "danger-full-access",
        "--output-last-message",
        str(output_path),
        "--skip-git-repo-check",
        "-",
    ]


def terminate_process_group(process: subprocess.Popen[str]) -> tuple[str, str]:
    os.killpg(process.pid, signal.SIGTERM)
    try:
        return process.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        return process.communicate()


def redact(text: str, secrets: list[str]) -> tuple[str, bool]:
    exposed = False
    for secret in secrets:
        if secret and secret in text:
            text = text.replace(secret, "[REDACTED]")
            exposed = True
    return text, exposed


def contamination_flags(stderr: str, runtime: Path, secret_exposed: bool) -> list[str]:
    flags: list[str] = []
    if re.search(r"advisor_answer_quality|answerquality_v\d|expected_|label_rationale", stderr):
        flags.append("evaluation_artifact_reference")
    if str(ROOT) in stderr:
        flags.append("original_repo_reference")
    if secret_exposed:
        flags.append("secret_exposure")
    for cwd in re.findall(r"\sin\s+(/[^\n]+)$", stderr, flags=re.MULTILINE):
        try:
            Path(cwd.strip()).resolve().relative_to(runtime.resolve())
        except (ValueError, OSError):
            flags.append("command_outside_trial_runtime")
            break
    return sorted(set(flags))


def _session_files(business_dir: Path) -> list[Path]:
    return sorted((business_dir / ".money-model-advisor" / "sessions").glob("*.json"))


def validate_session_for_case(case: dict[str, Any], session: dict[str, Any]) -> str | None:
    """Reject completed turns that did not execute the intended product path."""
    metadata = session.get("metadata")
    if isinstance(metadata, dict) and metadata.get("failed_search"):
        return "completed session records a failed source-material search"

    actions = session.get("actions", [])
    source_events = session.get("source_events", [])
    calculation_events = session.get("calculation_events", [])
    cited_ids = session.get("cited_chunk_ids", [])
    category = case["answer_category"]

    if category == "source_grounded":
        if "search_source_material" not in actions:
            return "source-grounded case did not record search_source_material"
        if not source_events:
            return "source-grounded case has no successful source event"
        if not cited_ids:
            return "source-grounded case cites no retrieved passage"
        for index, event in enumerate(source_events, start=1):
            if event.get("retrieval_backend") != "hybrid":
                return f"source-grounded source event {index} does not record hybrid retrieval"
    elif category == "calculation":
        if "calculate" not in actions or not calculation_events:
            return "calculation case has no deterministic calculation event"
        if source_events or cited_ids:
            return "calculation case unexpectedly searched source material"
    elif category == "clarification":
        if "clarify" not in actions:
            return "clarification case did not record clarify"
        if source_events or cited_ids:
            return "clarification case unexpectedly searched source material"
    return None


def _chunk_texts() -> dict[str, dict[str, Any]]:
    import sys

    sys.path.insert(0, str(ROOT / "src"))
    from money_model_architect.retrieval import CorpusIndex

    index = CorpusIndex.from_transcripts(ROOT / "corpus" / "transcripts", chunking="framework-aware")
    return {
        chunk.id: {
            "id": chunk.id,
            "chapter": chunk.chapter,
            "subjects": list(chunk.subjects),
            "text": chunk.text,
        }
        for chunk in index.chunks
    }


CHUNKS = _chunk_texts()


def audit_packet(case: dict[str, Any], fixture_snapshot: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    inspected_ids: list[str] = []
    for event in session.get("source_events", []):
        for chunk in event.get("chunks", []):
            chunk_id = chunk.get("id")
            if isinstance(chunk_id, str) and chunk_id not in inspected_ids:
                inspected_ids.append(chunk_id)
    cited_ids = [chunk_id for chunk_id in session.get("cited_chunk_ids", []) if isinstance(chunk_id, str)]
    evidence_ids = list(dict.fromkeys([*inspected_ids, *cited_ids]))
    answer = str(session.get("assistant_message") or "")
    return {
        "case_id": case["case_id"],
        "source_case_id": case["source_case_id"],
        "scenario_id": case["scenario_id"],
        "answer_category": case["answer_category"],
        "user_turn": case["user_turn"],
        "business_context_snapshot": session.get("snapshot", fixture_snapshot),
        "fixture_snapshot": fixture_snapshot,
        "actions": session.get("actions", []),
        "calculation_events": session.get("calculation_events", []),
        "source_events": session.get("source_events", []),
        "cited_chunk_ids": cited_ids,
        "assistant_message": answer,
        "answer_sha256": sha256_text(answer),
        "evidence_passages": [CHUNKS[chunk_id] for chunk_id in evidence_ids if chunk_id in CHUNKS],
        "missing_evidence_chunk_ids": [chunk_id for chunk_id in evidence_ids if chunk_id not in CHUNKS],
    }


def run_trial(model: str, case: dict[str, Any], runs_dir: Path, timeout: int, force: bool) -> dict[str, Any]:
    destination = runs_dir / case["case_id"]
    result_path = destination / "result.json"
    if result_path.exists() and not force:
        return json.loads(result_path.read_text(encoding="utf-8"))
    if destination.exists() and force:
        shutil.rmtree(destination)

    secret = _dotenv_value("OPENAI_API_KEY")
    with tempfile.TemporaryDirectory(prefix="mma-answer-quality-") as temp_name:
        temp_root = Path(temp_name)
        runtime = temp_root / "runtime"
        codex_home = temp_root / "codex-home"
        auth_secrets = prepare_isolated_codex_home(codex_home)
        copy_runtime(runtime, secret)
        business_dir = prepare_business_dir(case, runtime)
        fixture_snapshot = json.loads(
            (business_dir / ".money-model-advisor" / "business_snapshot.json").read_text(encoding="utf-8")
        )
        prompt = acting_prompt(case, runtime, business_dir)
        response_path = runtime / "codex_final.txt"
        sessions_before = set(_session_files(business_dir))

        started = time.perf_counter()
        process_env = os.environ.copy()
        process_env["CODEX_HOME"] = str(codex_home)
        process = subprocess.Popen(
            codex_command(model, runtime, response_path),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=runtime,
            env=process_env,
            start_new_session=True,
        )
        timed_out = False
        try:
            stdout, stderr = process.communicate(input=prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            stdout, stderr = terminate_process_group(process)
        latency_ms = round((time.perf_counter() - started) * 1000, 1)

        codex_final = response_path.read_text(encoding="utf-8") if response_path.exists() else ""
        all_secrets = [*auth_secrets, *([secret] if secret else [])]
        stdout, stdout_secret = redact(stdout, all_secrets)
        stderr, stderr_secret = redact(stderr, all_secrets)
        codex_final, final_secret = redact(codex_final, all_secrets)
        flags = contamination_flags(stderr, runtime, stdout_secret or stderr_secret or final_secret)

        new_sessions = [path for path in _session_files(business_dir) if path not in sessions_before]
        session: dict[str, Any] | None = None
        session_error: str | None = None
        if len(new_sessions) == 1:
            try:
                session = json.loads(new_sessions[0].read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                session_error = f"invalid session JSON: {exc}"
        else:
            session_error = f"expected one completed session, found {len(new_sessions)}"

        if session and session.get("user_message") != case["user_turn"]:
            session_error = "completed session user_message does not match case"
        if session and not session.get("assistant_message"):
            session_error = "completed session has no assistant_message"
        if session and not session_error:
            session_error = validate_session_for_case(case, session)

        valid = bool(
            not timed_out
            and process.returncode == 0
            and not flags
            and not session_error
            and session
        )
        result = {
            "case_id": case["case_id"],
            "source_case_id": case["source_case_id"],
            "scenario_id": case["scenario_id"],
            "answer_category": case["answer_category"],
            "model": model,
            "valid": valid,
            "timed_out": timed_out,
            "returncode": process.returncode,
            "latency_ms": latency_ms,
            "contamination_flags": flags,
            "session_error": session_error,
            "created_at": utc_now(),
        }

        destination.mkdir(parents=True, exist_ok=True)
        (destination / "acting_prompt.md").write_text(prompt, encoding="utf-8")
        (destination / "codex_stdout.txt").write_text(stdout, encoding="utf-8")
        (destination / "codex_stderr.txt").write_text(stderr, encoding="utf-8")
        (destination / "codex_final.txt").write_text(codex_final, encoding="utf-8")
        write_json(destination / "fixture_snapshot.json", fixture_snapshot)
        if session:
            write_json(destination / "session_record.json", session)
            write_json(destination / "audit_packet.json", audit_packet(case, fixture_snapshot, session))
        write_json(result_path, result)
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--max-workers", type=int, default=2)
    parser.add_argument("--case-id", action="append")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    cases = load_jsonl(args.cases)
    errors = validate_cases(cases)
    if errors:
        raise SystemExit("invalid answer-quality suite:\n- " + "\n- ".join(errors))
    if args.case_id:
        selected = set(args.case_id)
        cases = [case for case in cases if case["case_id"] in selected]

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as executor:
        futures = {
            executor.submit(run_trial, args.model, case, args.runs_dir, args.timeout, args.force): case["case_id"]
            for case in cases
        }
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(
                f"completed {result['case_id']}: valid={result['valid']} "
                f"latency={result['latency_ms'] / 1000:.1f}s",
                flush=True,
            )
    results.sort(key=lambda row: row["case_id"])
    write_json(
        args.runs_dir / "run_summary.json",
        {
            "created_at": utc_now(),
            "model": args.model,
            "cases_path": str(args.cases.relative_to(ROOT)),
            "cases_sha256": hashlib.sha256(args.cases.read_bytes()).hexdigest(),
            "results": results,
        },
    )
    return 0 if all(result["valid"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
