"""Build the synthetic CI warehouse from the committed fixture file.

The fixture goes through the real pipeline code (parse then load), so the
CI dbt build exercises the same path as production, on data that contains
no real record. One duplicate pair, one partial date, one bad sex code and
one short line are there on purpose - tests that never catch anything
prove nothing.
"""

from pathlib import Path

from drm import parse, warehouse

FIXTURE = Path(__file__).parent / "deces-fixture.txt"
DB_PATH = Path("data/ci_warehouse.duckdb")


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    parquet_path = DB_PATH.parent / "ci_fixture.parquet"
    quarantine_path = DB_PATH.parent / "ci_quarantine.jsonl"
    stats = parse.parse_file(FIXTURE, "fixture-hash", parquet_path, quarantine_path)
    con = warehouse.connect(DB_PATH)
    load_stats = warehouse.load_raw(con, parquet_path, "fixture-hash")
    print(
        f"fixture: {stats['rows']} rows parsed, "
        f"{stats['quarantined']} quarantined, "
        f"{load_stats['inserted']} loaded into {DB_PATH}"
    )


if __name__ == "__main__":
    main()
