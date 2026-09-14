import json

from typer.testing import CliRunner

from drm.cli import app
from drm.config import DATASET_API

runner = CliRunner()

FILE_URL = "https://example.org/deces-2026-m08.txt"
DATASET_JSON = {"resources": [{"title": "deces-2026-m08.txt", "url": FILE_URL}]}
GOOD = "M" * 176
TRAILING = GOOD + "X" * 22  # INSEE: trailing non-significant characters
BAD = "TROP COURT"
CONTENT = (GOOD + "\n" + TRAILING + "\n" + BAD + "\n").encode()


def test_dry_run_downloads_nothing(httpx_mock, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    httpx_mock.add_response(url=DATASET_API, json=DATASET_JSON)
    result = runner.invoke(app, ["ingest", "deaths", "--month", "2026-08", "--dry-run"])
    assert result.exit_code == 0
    assert "dry-run" in result.output
    assert not (tmp_path / "data").exists()


def test_ingest_writes_raw_and_manifest(httpx_mock, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    httpx_mock.add_response(url=DATASET_API, json=DATASET_JSON)
    httpx_mock.add_response(url=FILE_URL, content=CONTENT)

    result = runner.invoke(app, ["ingest", "deaths", "--month", "2026-08"])
    assert result.exit_code == 0

    raw_file = tmp_path / "data" / "raw" / "deces-2026-m08.txt"
    assert raw_file.read_bytes() == CONTENT

    manifest_lines = (
        (tmp_path / "data" / "manifest.jsonl").read_text().strip().splitlines()
    )
    assert len(manifest_lines) == 1
    entry = json.loads(manifest_lines[0])
    assert entry["period"] == "2026-08"
    assert entry["lines"] == 3
    assert entry["bad_lines"] == 1


def test_rerun_same_content_is_idempotent(httpx_mock, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    httpx_mock.add_response(url=DATASET_API, json=DATASET_JSON)
    httpx_mock.add_response(url=FILE_URL, content=CONTENT)
    httpx_mock.add_response(url=DATASET_API, json=DATASET_JSON)
    httpx_mock.add_response(url=FILE_URL, content=CONTENT)

    first = runner.invoke(app, ["ingest", "deaths", "--month", "2026-08"])
    second = runner.invoke(app, ["ingest", "deaths", "--month", "2026-08"])
    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "unchanged" in second.output

    manifest_lines = (
        (tmp_path / "data" / "manifest.jsonl").read_text().strip().splitlines()
    )
    assert len(manifest_lines) == 1


def test_republication_creates_new_version(httpx_mock, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    changed = (GOOD + "\n").encode()
    httpx_mock.add_response(url=DATASET_API, json=DATASET_JSON)
    httpx_mock.add_response(url=FILE_URL, content=CONTENT)
    httpx_mock.add_response(url=DATASET_API, json=DATASET_JSON)
    httpx_mock.add_response(url=FILE_URL, content=changed)

    runner.invoke(app, ["ingest", "deaths", "--month", "2026-08"])
    result = runner.invoke(app, ["ingest", "deaths", "--month", "2026-08"])
    assert result.exit_code == 0

    raw_dir = tmp_path / "data" / "raw"
    assert (raw_dir / "deces-2026-m08.txt").read_bytes() == CONTENT
    assert (raw_dir / "deces-2026-m08.txt.v2").read_bytes() == changed

    manifest_lines = (
        (tmp_path / "data" / "manifest.jsonl").read_text().strip().splitlines()
    )
    assert len(manifest_lines) == 2
