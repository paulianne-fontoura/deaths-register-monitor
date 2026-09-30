from datetime import date
from types import SimpleNamespace

import duckdb
import pytest
from typer.testing import CliRunner

from drm import publish
from drm.cli import app


def _warehouse(path, extra_column=""):
    con = duckdb.connect(str(path))
    con.execute(
        "create table fct_monthly_quality as select"
        f" date '2026-01-01' as mois_deces, 70504::bigint as n_deces{extra_column}"
    )
    con.execute(
        "create table fct_completeness_triangle as select 'x' as triangle_id,"
        " date '2026-01-01' as mois_deces"
    )
    con.execute(
        "create table fct_department_quality as select '75' as departement,"
        " 2025 as annee_deces"
    )
    con.execute("create table qa_reconciliation as select 2025 as annee")
    return con


def test_export_writes_parquet_with_utc_timestamp(tmp_path):
    con = _warehouse(tmp_path / "w.duckdb")
    files = publish.export_marts(con, tmp_path / "out", publish.PUBLISHABLE_MARTS)
    assert [mart for mart, _, _ in files] == list(publish.PUBLISHABLE_MARTS)
    first = files[0][1]
    row = duckdb.sql(
        f"select mois_deces, n_deces, typeof(_exported_at) from '{first.as_posix()}'"
    ).fetchone()
    assert row[0] == date(2026, 1, 1)
    assert row[1] == 70504
    assert row[2] == "TIMESTAMP WITH TIME ZONE"  # BigQuery TIMESTAMP, not DATETIME


def test_export_refuses_nominative_column(tmp_path):
    con = _warehouse(tmp_path / "w.duckdb", extra_column=", 'X' as full_name")
    with pytest.raises(publish.NominativeColumnError, match="full_name"):
        publish.export_marts(con, tmp_path / "out", ("fct_monthly_quality",))
    assert not (tmp_path / "out" / "fct_monthly_quality.parquet").exists()


def test_export_refuses_mart_outside_allowlist(tmp_path):
    con = _warehouse(tmp_path / "w.duckdb")
    with pytest.raises(publish.NominativeColumnError, match="allowlist"):
        publish.export_marts(con, tmp_path / "out", ("fct_death_records",))


def test_load_replaces_each_table_in_the_export_dataset(tmp_path):
    parquet = tmp_path / "m.parquet"
    parquet.write_bytes(b"PAR1")
    calls = []

    class FakeClient:
        project = "my-proj"

        def create_dataset(self, dataset, exists_ok):
            calls.append(("dataset", dataset.id, dataset.location, exists_ok))

        def load_table_from_file(self, handle, table_id, job_config, location):
            calls.append(("load", table_id, job_config.write_disposition, location))
            return SimpleNamespace(result=lambda: None, output_rows=42)

    class FakeDataset:
        def __init__(self, dataset_id):
            self.id = dataset_id
            self.location = None

    fake_bq = SimpleNamespace(
        Dataset=FakeDataset,
        LoadJobConfig=lambda **kwargs: SimpleNamespace(**kwargs),
        SourceFormat=SimpleNamespace(PARQUET="PARQUET"),
        WriteDisposition=SimpleNamespace(WRITE_TRUNCATE="WRITE_TRUNCATE"),
    )
    loaded = publish.load_to_bigquery(
        FakeClient(), fake_bq, [("fct_monthly_quality", parquet, 1)]
    )
    assert loaded == [("my-proj.drm_exports.fct_monthly_quality", 42)]
    assert calls[0] == ("dataset", "my-proj.drm_exports", "EU", True)
    assert calls[1][2] == "WRITE_TRUNCATE"  # load job, no DML (sandbox)


def test_publish_dry_run_loads_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    _warehouse(tmp_path / "data" / "warehouse.duckdb").close()
    monkeypatch.delenv("DBT_BQ_PROJECT", raising=False)
    result = CliRunner().invoke(app, ["publish", "--dry-run"])
    assert result.exit_code == 0, result.output
    assert result.output.count("exported:") == 4
    assert "nothing loaded" in result.output
