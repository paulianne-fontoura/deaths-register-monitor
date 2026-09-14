"""Warehouse tests: idempotence, no deletion, duplicates kept (ADR-005)."""

import pyarrow as pa
import pyarrow.parquet as pq

from drm import warehouse

COLUMNS = [
    "nom_prenoms",
    "sexe",
    "date_naissance",
    "code_lieu_naissance",
    "commune_naissance",
    "pays_naissance",
    "date_deces",
    "code_lieu_deces",
    "numero_acte",
    "_line_number",
    "_row_hash",
    "_source_file",
    "_file_hash",
    "_ingested_at",
]


def make_row(line_number=1, row_hash="hash-a", file_hash="file-1"):
    return {
        "nom_prenoms": "MARTIN*JEAN/",
        "sexe": "1",
        "date_naissance": "19381215",
        "code_lieu_naissance": "75056",
        "commune_naissance": "PARIS",
        "pays_naissance": "",
        "date_deces": "20260812",
        "code_lieu_deces": "75056",
        "numero_acte": "181",
        "_line_number": line_number,
        "_row_hash": row_hash,
        "_source_file": "deces-test.txt",
        "_file_hash": file_hash,
        "_ingested_at": "2026-09-14T00:00:00+00:00",
    }


def write_parquet(path, rows):
    table = pa.table({column: [row[column] for row in rows] for column in COLUMNS})
    pq.write_table(table, path)


def test_load_inserts_rows_and_logs(tmp_path):
    parquet = tmp_path / "f1.parquet"
    write_parquet(parquet, [make_row(1, "hash-a"), make_row(2, "hash-b")])
    con = warehouse.connect(tmp_path / "wh.duckdb")

    stats = warehouse.load_raw(con, parquet, "file-1")

    assert stats["rows_in_file"] == 2
    assert stats["inserted"] == 2
    assert warehouse.count_rows(con) == 2
    assert warehouse.is_loaded(con, "file-1")
    assert not warehouse.is_loaded(con, "file-2")


def test_second_load_adds_nothing(tmp_path):
    parquet = tmp_path / "f1.parquet"
    write_parquet(parquet, [make_row(1, "hash-a"), make_row(2, "hash-b")])
    con = warehouse.connect(tmp_path / "wh.duckdb")

    warehouse.load_raw(con, parquet, "file-1")
    stats = warehouse.load_raw(con, parquet, "file-1")

    assert stats["inserted"] == 0
    assert warehouse.count_rows(con) == 2


def test_duplicate_lines_inside_one_file_are_kept(tmp_path):
    # Two identical lines in one delivery share a _row_hash. They are real
    # register content: keep both, count and flag later (ADR-005).
    parquet = tmp_path / "f1.parquet"
    write_parquet(parquet, [make_row(1, "hash-a"), make_row(2, "hash-a")])
    con = warehouse.connect(tmp_path / "wh.duckdb")

    stats = warehouse.load_raw(con, parquet, "file-1")

    assert stats["inserted"] == 2


def test_same_line_in_two_files_is_kept(tmp_path):
    # The same record republished in another file is a distinct snapshot:
    # (_file_hash, _row_hash) differs, so both copies stay.
    first = tmp_path / "f1.parquet"
    second = tmp_path / "f2.parquet"
    write_parquet(first, [make_row(1, "hash-a", "file-1")])
    write_parquet(second, [make_row(1, "hash-a", "file-2")])
    con = warehouse.connect(tmp_path / "wh.duckdb")

    warehouse.load_raw(con, first, "file-1")
    stats = warehouse.load_raw(con, second, "file-2")

    assert stats["inserted"] == 1
    assert warehouse.count_rows(con) == 2
