"""Publish the aggregate marts to BigQuery (ADR-010).

The nominative register never leaves the workstation (ADR-009). Only the
marts on the allowlist below are exported, and every export is checked
against a denylist of nominative columns before anything is written - the
frontier is enforced in code, not by convention. Exports are parquet files
loaded with load jobs (WRITE_TRUNCATE), the only write path the BigQuery
sandbox allows (no DML, no streaming).
"""

from pathlib import Path
from types import ModuleType
from typing import Any

import duckdb

PUBLISHABLE_MARTS = (
    "fct_monthly_quality",
    "fct_completeness_triangle",
    "fct_department_quality",
    "qa_reconciliation",
)

NOMINATIVE_COLUMNS = frozenset(
    {
        "full_name",
        "name_normalized",
        "birth_date",
        "birth_date_raw",
        "birth_place_code",
        "birth_commune",
        "birth_country",
        "death_date",
        "death_date_raw",
        "death_place_code",
        "certificate_number",
        "record_id",
        "row_hash",
        "key_person",
        "key_event",
    }
)

EXPORT_DATASET = "drm_exports"
LOCATION = "EU"


class NominativeColumnError(Exception):
    """A mart about to be published carries a nominative column."""


def _mart_schema(con: duckdb.DuckDBPyConnection, mart: str) -> str | None:
    row = con.execute(
        "select table_schema from information_schema.tables where table_name = ?",
        [mart],
    ).fetchone()
    return row[0] if row else None


def export_marts(
    con: duckdb.DuckDBPyConnection, export_dir: Path, marts: tuple[str, ...]
) -> list[tuple[str, Path, int]]:
    """Write each allowed mart to parquet with an _exported_at UTC timestamp.

    Returns (mart, parquet path, rows). Refuses any mart outside the
    allowlist and any mart carrying a nominative column. The timestamp is
    TIMESTAMPTZ so parquet marks it UTC-adjusted and BigQuery reads it as
    TIMESTAMP, not DATETIME.
    """
    export_dir.mkdir(parents=True, exist_ok=True)
    exported: list[tuple[str, Path, int]] = []
    for mart in marts:
        if mart not in PUBLISHABLE_MARTS:
            raise NominativeColumnError(f"{mart} is not on the publication allowlist")
        schema = _mart_schema(con, mart)
        if schema is None:
            raise FileNotFoundError(f"{mart} not found in the warehouse, run dbt build")
        columns = {
            row[0]
            for row in con.execute(
                "select column_name from information_schema.columns"
                " where table_schema = ? and table_name = ?",
                [schema, mart],
            ).fetchall()
        }
        leaked = sorted(columns & NOMINATIVE_COLUMNS)
        if leaked:
            raise NominativeColumnError(f"{mart} carries {', '.join(leaked)}")
        target = export_dir / f"{mart}.parquet"
        con.execute(
            f"copy (select *, current_timestamp as _exported_at"
            f" from {schema}.{mart}) to '{target.as_posix()}' (format parquet)"
        )
        rows = con.execute(f"select count(*) from {schema}.{mart}").fetchone()[0]
        exported.append((mart, target, rows))
    return exported


def load_to_bigquery(
    client: Any, bq: ModuleType, files: list[tuple[str, Path, int]]
) -> list[tuple[str, int]]:
    """Load the parquet exports into the export dataset, replacing each table.

    `bq` is the google.cloud.bigquery module, passed in so the CLI imports it
    lazily and the tests can stand in a fake. Returns (table id, rows loaded).
    """
    dataset = bq.Dataset(f"{client.project}.{EXPORT_DATASET}")
    dataset.location = LOCATION
    client.create_dataset(dataset, exists_ok=True)
    config = bq.LoadJobConfig(
        source_format=bq.SourceFormat.PARQUET,
        write_disposition=bq.WriteDisposition.WRITE_TRUNCATE,
    )
    loaded: list[tuple[str, int]] = []
    for mart, path, _ in files:
        table_id = f"{client.project}.{EXPORT_DATASET}.{mart}"
        with open(path, "rb") as handle:
            job = client.load_table_from_file(
                handle, table_id, job_config=config, location=LOCATION
            )
        job.result()
        loaded.append((table_id, job.output_rows))
    return loaded
