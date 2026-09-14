"""DuckDB warehouse - the queryable face of the raw layer.

load_raw() inserts only rows whose (_file_hash, _row_hash) pair is not in
the table yet, and never deletes anything. Every snapshot stays as
published; duplicate lines inside one file are kept, counted and flagged
later (ADR-005). Loading the same file twice therefore adds zero rows.
"""

import time
from datetime import UTC, datetime
from pathlib import Path

import duckdb

RAW_DDL = """
CREATE TABLE IF NOT EXISTS raw_deces (
    nom_prenoms VARCHAR,
    sexe VARCHAR,
    date_naissance VARCHAR,
    code_lieu_naissance VARCHAR,
    commune_naissance VARCHAR,
    pays_naissance VARCHAR,
    date_deces VARCHAR,
    code_lieu_deces VARCHAR,
    numero_acte VARCHAR,
    _line_number BIGINT,
    _row_hash VARCHAR,
    _source_file VARCHAR,
    _file_hash VARCHAR,
    _ingested_at VARCHAR
)
"""

LOG_DDL = """
CREATE TABLE IF NOT EXISTS load_log (
    file_hash VARCHAR,
    source_file VARCHAR,
    rows_in_file BIGINT,
    rows_inserted BIGINT,
    seconds DOUBLE,
    loaded_at VARCHAR
)
"""


def connect(db_path: Path) -> duckdb.DuckDBPyConnection:
    """Open (or create) the warehouse and make sure both tables exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute(RAW_DDL)
    con.execute(LOG_DDL)
    return con


def is_loaded(con: duckdb.DuckDBPyConnection, file_hash: str) -> bool:
    """True when this exact file content already went through load_raw."""
    row = con.execute(
        "SELECT 1 FROM load_log WHERE file_hash = ? LIMIT 1", [file_hash]
    ).fetchone()
    return row is not None


def count_rows(con: duckdb.DuckDBPyConnection) -> int:
    return con.execute("SELECT count(*) FROM raw_deces").fetchone()[0]


def load_raw(
    con: duckdb.DuckDBPyConnection, parquet_path: Path, file_hash: str
) -> dict:
    """Load one parquet file, inserting only unknown (_file_hash, _row_hash) rows.

    The insert and its load_log line commit in one transaction, so a crash
    cannot leave a file half loaded but marked as done.
    Returns stats: rows_in_file, inserted, seconds.
    """
    start = time.perf_counter()
    con.execute("BEGIN")
    try:
        before = count_rows(con)
        con.execute(
            """
            INSERT INTO raw_deces BY NAME
            SELECT src.* FROM read_parquet(?) src
            ANTI JOIN raw_deces existing
            ON src._file_hash = existing._file_hash
            AND src._row_hash = existing._row_hash
            """,
            [str(parquet_path)],
        )
        inserted = count_rows(con) - before
        rows_in_file = con.execute(
            "SELECT count(*) FROM read_parquet(?)", [str(parquet_path)]
        ).fetchone()[0]
        seconds = round(time.perf_counter() - start, 2)
        con.execute(
            "INSERT INTO load_log VALUES (?, ?, ?, ?, ?, ?)",
            [
                file_hash,
                parquet_path.name.removesuffix(".parquet"),
                rows_in_file,
                inserted,
                seconds,
                datetime.now(UTC).isoformat(timespec="seconds"),
            ],
        )
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    return {"rows_in_file": rows_in_file, "inserted": inserted, "seconds": seconds}
