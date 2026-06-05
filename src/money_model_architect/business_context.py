"""Local business directory sync and advisor state paths."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .snapshot import BusinessSnapshot

STATE_DIR_NAME = ".money-model-advisor"
CONTEXT_MANIFEST_FILE = "context_manifest.json"
SNAPSHOT_FILE = "business_snapshot.json"
SESSIONS_DIR = "sessions"

SUPPORTED_CONTEXT_EXTENSIONS = {
    ".csv",
    ".json",
    ".md",
    ".markdown",
    ".txt",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class AdvisorPaths:
    business_dir: Path
    state_dir: Path
    context_manifest: Path
    snapshot: Path
    sessions_dir: Path


@dataclass
class ContextFileRecord:
    path: str
    sha256: str
    size_bytes: int
    mtime_ns: int
    status: str = "parsed"
    error: str | None = None


@dataclass
class ContextManifest:
    schema_version: str = "context_manifest.v1"
    synced_at: str = ""
    files: list[ContextFileRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ContextManifest":
        return cls(
            schema_version=payload.get("schema_version", "context_manifest.v1"),
            synced_at=payload.get("synced_at", ""),
            files=[ContextFileRecord(**item) for item in payload.get("files", [])],
        )

    @classmethod
    def load(cls, path: Path) -> "ContextManifest":
        if not path.exists():
            return cls()
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def advisor_paths(business_dir: Path) -> AdvisorPaths:
    root = business_dir.expanduser().resolve()
    state_dir = root / STATE_DIR_NAME
    return AdvisorPaths(
        business_dir=root,
        state_dir=state_dir,
        context_manifest=state_dir / CONTEXT_MANIFEST_FILE,
        snapshot=state_dir / SNAPSHOT_FILE,
        sessions_dir=state_dir / SESSIONS_DIR,
    )


def ensure_advisor_state(paths: AdvisorPaths) -> None:
    paths.business_dir.mkdir(parents=True, exist_ok=True)
    paths.state_dir.mkdir(parents=True, exist_ok=True)
    paths.sessions_dir.mkdir(parents=True, exist_ok=True)
    if not paths.snapshot.exists():
        BusinessSnapshot().save(paths.snapshot)


def sync_business_context(business_dir: Path) -> tuple[ContextManifest, dict[str, int]]:
    paths = advisor_paths(business_dir)
    ensure_advisor_state(paths)
    previous = ContextManifest.load(paths.context_manifest)
    previous_hashes = {record.path: record.sha256 for record in previous.files}

    records: list[ContextFileRecord] = []
    for path in iter_context_files(paths.business_dir):
        relative = path.relative_to(paths.business_dir).as_posix()
        try:
            digest = sha256_file(path)
            stat = path.stat()
            records.append(
                ContextFileRecord(
                    path=relative,
                    sha256=digest,
                    size_bytes=stat.st_size,
                    mtime_ns=stat.st_mtime_ns,
                )
            )
        except OSError as exc:
            records.append(ContextFileRecord(path=relative, sha256="", size_bytes=0, mtime_ns=0, status="error", error=str(exc)))

    manifest = ContextManifest(synced_at=utc_now(), files=records)
    manifest.save(paths.context_manifest)

    current_hashes = {record.path: record.sha256 for record in records}
    changed = sum(1 for path, digest in current_hashes.items() if previous_hashes.get(path) != digest)
    removed = sum(1 for path in previous_hashes if path not in current_hashes)
    unchanged = sum(1 for path, digest in current_hashes.items() if previous_hashes.get(path) == digest)
    return manifest, {"changed": changed, "removed": removed, "unchanged": unchanged, "total": len(records)}


def iter_context_files(business_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in business_dir.rglob("*"):
        if not path.is_file():
            continue
        if STATE_DIR_NAME in path.parts:
            continue
        if path.name.startswith("."):
            continue
        if path.suffix.lower() not in SUPPORTED_CONTEXT_EXTENSIONS:
            continue
        files.append(path)
    return sorted(files)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
