"""COG referential download: files written, manifest history, idempotence."""

from typer.testing import CliRunner

from drm.cli import app
from drm.cog import COG_FILES
from drm.config import COG_BASE_URL

runner = CliRunner()


def mock_all_files(httpx_mock, suffix=b"v1"):
    for name in COG_FILES:
        httpx_mock.add_response(
            url=COG_BASE_URL + name, content=name.encode() + b";" + suffix
        )


def test_dry_run_downloads_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["cog", "--dry-run"])
    assert result.exit_code == 0
    assert "v_commune_depuis_1943.csv" in result.output
    assert not (tmp_path / "data").exists()


def test_cog_downloads_all_files_with_manifest(httpx_mock, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mock_all_files(httpx_mock)

    result = runner.invoke(app, ["cog"])

    assert result.exit_code == 0
    cog_dir = tmp_path / "data" / "reference" / "cog"
    for name in COG_FILES:
        assert (cog_dir / name).exists()
    manifest_lines = (
        (tmp_path / "data" / "manifest.jsonl").read_text().strip().splitlines()
    )
    assert len(manifest_lines) == len(COG_FILES)
    assert result.output.count(": new") == len(COG_FILES)


def test_rerun_same_content_is_unchanged(httpx_mock, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mock_all_files(httpx_mock)
    runner.invoke(app, ["cog"])

    mock_all_files(httpx_mock)
    result = runner.invoke(app, ["cog"])

    assert result.exit_code == 0
    assert result.output.count(": unchanged") == len(COG_FILES)
    manifest_lines = (
        (tmp_path / "data" / "manifest.jsonl").read_text().strip().splitlines()
    )
    assert len(manifest_lines) == len(COG_FILES)


def test_republished_file_replaces_and_keeps_history(httpx_mock, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mock_all_files(httpx_mock)
    runner.invoke(app, ["cog"])

    mock_all_files(httpx_mock, suffix=b"v2")
    result = runner.invoke(app, ["cog"])

    assert result.exit_code == 0
    assert result.output.count(": new") == len(COG_FILES)
    first = (tmp_path / "data" / "reference" / "cog" / COG_FILES[0]).read_bytes()
    assert first.endswith(b"v2")  # live file replaced
    manifest_lines = (
        (tmp_path / "data" / "manifest.jsonl").read_text().strip().splitlines()
    )
    assert len(manifest_lines) == 2 * len(COG_FILES)  # history kept
