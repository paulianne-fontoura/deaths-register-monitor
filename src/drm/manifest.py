"""Append-only manifest of every ingested file (ADR-003).

One JSON line per ingestion: period, title, url, sha256, bytes, line counts,
final path and timestamp. The manifest is the memory that makes reruns safe.
"""

import json
from pathlib import Path, PureWindowsPath


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def local_path(entry: dict) -> Path:
    """The entry's raw file on this machine, whichever system wrote the line.

    The manifest is versioned (ADR-009) and written on Windows, so stored
    paths may carry backslashes. Both separators are read as separators.
    """
    return Path(PureWindowsPath(entry["path"]).as_posix())


def append(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def seen(entries: list[dict], title: str, sha256: str) -> bool:
    """True when this exact file content was already ingested."""
    return any(e.get("title") == title and e.get("sha256") == sha256 for e in entries)


def latest(entries: list[dict], title: str) -> dict | None:
    """Most recent entry for a title. The manifest is append-only, so last wins."""
    found = None
    for entry in entries:
        if entry.get("title") == title:
            found = entry
    return found


def next_version_path(raw_dir: Path, title: str) -> Path:
    """First free name: title, then title.v2, title.v3... Never overwrite (ADR-003)."""
    candidate = raw_dir / title
    version = 1
    while candidate.exists():
        version += 1
        candidate = raw_dir / f"{title}.v{version}"
    return candidate
