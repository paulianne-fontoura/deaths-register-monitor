"""Streaming download with retries, to a temporary file, with SHA-256."""

import hashlib
from pathlib import Path

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


@retry(
    retry=retry_if_exception_type(httpx.TransportError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, max=30),
    reraise=True,
)
def fetch_to_temp(
    client: httpx.Client, url: str, raw_dir: Path
) -> tuple[Path, str, int]:
    """Download url into raw_dir as a .part file.

    Returns (temp_path, sha256, size). The caller decides the final name,
    so the idempotence rule of ADR-003 stays in one place (the CLI).
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    temp_path = raw_dir / "download.part"
    digest = hashlib.sha256()
    size = 0
    with client.stream("GET", url, timeout=120, follow_redirects=True) as response:
        response.raise_for_status()
        with open(temp_path, "wb") as handle:
            for chunk in response.iter_bytes(65536):
                handle.write(chunk)
                digest.update(chunk)
                size += len(chunk)
    return temp_path, digest.hexdigest(), size
