"""Backfill tests: plan, full load, resume, range, failure isolation."""

import hashlib
import json

import httpx
from typer.testing import CliRunner

from drm import warehouse
from drm.cli import app
from drm.config import DATASET_API, Settings

runner = CliRunner()

URL_1970 = "https://example.org/deces-1970.txt"
URL_1971 = "https://example.org/deces-1971.txt"
URL_M01 = "https://example.org/deces-2026-m01.txt"

DATASET_JSON = {
    "resources": [
        {"title": "deces-2026-t1.txt", "url": "https://example.org/t1.txt"},
        {"title": "deces-2026-m01.txt", "url": URL_M01},
        {"title": "deces-1971.txt", "url": URL_1971},
        {"title": "deces-1970.txt", "url": URL_1970},
        {"title": "Fichier des oppositions", "url": "https://example.org/opp.csv"},
    ]
}

CONTENT_1970 = ("A" * 176 + "\n" + "B" * 176 + "\n").encode()
CONTENT_1971 = ("C" * 176 + "\n").encode()
CONTENT_M01 = ("D" * 176 + "\n" + "E" * 176 + "\n" + "F" * 176 + "\n").encode()


def mock_all(httpx_mock):
    httpx_mock.add_response(url=DATASET_API, json=DATASET_JSON)
    httpx_mock.add_response(url=URL_1970, content=CONTENT_1970)
    httpx_mock.add_response(url=URL_1971, content=CONTENT_1971)
    httpx_mock.add_response(url=URL_M01, content=CONTENT_M01)


def test_dry_run_plans_in_order_and_downloads_nothing(
    httpx_mock, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    httpx_mock.add_response(url=DATASET_API, json=DATASET_JSON)

    result = runner.invoke(app, ["backfill", "deaths", "--dry-run"])

    assert result.exit_code == 0
    assert "plan: 3 files" in result.output
    assert (
        result.output.index("deces-1970.txt")
        < result.output.index("deces-1971.txt")
        < result.output.index("deces-2026-m01.txt")
    )
    assert "t1" not in result.output
    assert "oppositions" not in result.output
    assert not (tmp_path / "data").exists()


def test_backfill_downloads_parses_and_loads_everything(
    httpx_mock, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    mock_all(httpx_mock)

    result = runner.invoke(app, ["backfill", "deaths"])

    assert result.exit_code == 0
    settings = Settings()
    assert (settings.raw_dir / "deces-1970.txt").read_bytes() == CONTENT_1970
    assert (settings.data_dir / "parquet" / "deces-1971.txt.parquet").exists()
    manifest_lines = settings.manifest_path.read_text().strip().splitlines()
    assert len(manifest_lines) == 3
    assert json.loads(manifest_lines[0])["period"] == "1970"
    assert json.loads(manifest_lines[2])["period"] == "2026-01"
    con = warehouse.connect(settings.warehouse_path)
    assert warehouse.count_rows(con) == 6
    assert "warehouse: 6 rows" in result.output


def test_rerun_downloads_nothing_and_adds_nothing(httpx_mock, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mock_all(httpx_mock)
    runner.invoke(app, ["backfill", "deaths"])

    # Only the dataset listing is mocked for the second run: any download
    # attempt would hit an unmatched request and fail the test.
    httpx_mock.add_response(url=DATASET_API, json=DATASET_JSON)
    result = runner.invoke(app, ["backfill", "deaths"])

    assert result.exit_code == 0
    assert result.output.count("already loaded") == 3
    con = warehouse.connect(Settings().warehouse_path)
    assert warehouse.count_rows(con) == 6


def test_backfill_respects_year_range(httpx_mock, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    httpx_mock.add_response(url=DATASET_API, json=DATASET_JSON)
    httpx_mock.add_response(url=URL_1971, content=CONTENT_1971)

    result = runner.invoke(
        app, ["backfill", "deaths", "--from", "1971", "--to", "1971"]
    )

    assert result.exit_code == 0
    settings = Settings()
    assert (settings.raw_dir / "deces-1971.txt").exists()
    assert not (settings.raw_dir / "deces-1970.txt").exists()


def test_one_failure_does_not_stop_the_others(httpx_mock, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    httpx_mock.add_response(url=DATASET_API, json=DATASET_JSON)
    for _ in range(3):  # the download retries twice before giving up
        httpx_mock.add_exception(httpx.ConnectError("network down"), url=URL_1970)
    httpx_mock.add_response(url=URL_1971, content=CONTENT_1971)
    httpx_mock.add_response(url=URL_M01, content=CONTENT_M01)

    result = runner.invoke(app, ["backfill", "deaths"])

    assert result.exit_code == 1
    assert "FAILED" in result.output
    assert "failed:    deces-1970.txt" in result.output
    con = warehouse.connect(Settings().warehouse_path)
    assert warehouse.count_rows(con) == 4  # 1971 and 2026-m01 still loaded


def test_all_deliveries_plans_monthly_overlaps(httpx_mock, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    dataset = {
        "resources": [
            {"title": "deces-1970.txt", "url": URL_1970},
            {"title": "deces-1970-m01.txt", "url": "https://example.org/m01-1970.txt"},
        ]
    }
    httpx_mock.add_response(url=DATASET_API, json=dataset)

    result = runner.invoke(app, ["backfill", "deaths", "--dry-run", "--all-deliveries"])

    assert result.exit_code == 0
    assert "plan: 2 files" in result.output
    assert result.output.index("deces-1970.txt") < result.output.index(
        "deces-1970-m01.txt"
    )


def test_fresh_clone_of_the_versioned_manifest(httpx_mock, tmp_path, monkeypatch):
    # The manifest is tracked in git (ADR-009) and written on Windows. On a
    # fresh clone its entries point at raw files that are not there - the
    # backfill must download them, keep them where the manifest says, load
    # them, and leave the shared manifest untouched.
    monkeypatch.chdir(tmp_path)
    settings = Settings()
    settings.manifest_path.parent.mkdir(parents=True)
    captured = [
        ("1970", "deces-1970.txt", URL_1970, CONTENT_1970),
        ("1971", "deces-1971.txt", URL_1971, CONTENT_1971),
        ("2026-01", "deces-2026-m01.txt", URL_M01, CONTENT_M01),
    ]
    lines = [
        json.dumps(
            {
                "period": period,
                "title": title,
                "url": url,
                "path": f"data\\raw\\{title}",
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
        for period, title, url, content in captured
    ]
    settings.manifest_path.write_text("\n".join(lines) + "\n")
    mock_all(httpx_mock)

    result = runner.invoke(app, ["backfill", "deaths"])

    assert result.exit_code == 0, result.output
    assert (settings.raw_dir / "deces-1970.txt").read_bytes() == CONTENT_1970
    assert settings.manifest_path.read_text().strip().splitlines() == lines
    con = warehouse.connect(settings.warehouse_path)
    assert warehouse.count_rows(con) == 6
