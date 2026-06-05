"""Advisor state paths and initialization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .snapshot import BusinessSnapshot

STATE_DIR_NAME = ".money-model-advisor"
SNAPSHOT_FILE = "business_snapshot.json"
SESSIONS_DIR = "sessions"


@dataclass(frozen=True)
class AdvisorPaths:
    business_dir: Path
    state_dir: Path
    snapshot: Path
    sessions_dir: Path


def advisor_paths(business_dir: Path) -> AdvisorPaths:
    root = business_dir.expanduser().resolve()
    state_dir = root / STATE_DIR_NAME
    return AdvisorPaths(
        business_dir=root,
        state_dir=state_dir,
        snapshot=state_dir / SNAPSHOT_FILE,
        sessions_dir=state_dir / SESSIONS_DIR,
    )


def ensure_advisor_state(paths: AdvisorPaths) -> None:
    paths.business_dir.mkdir(parents=True, exist_ok=True)
    paths.state_dir.mkdir(parents=True, exist_ok=True)
    paths.sessions_dir.mkdir(parents=True, exist_ok=True)
    if not paths.snapshot.exists():
        BusinessSnapshot().save(paths.snapshot)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
