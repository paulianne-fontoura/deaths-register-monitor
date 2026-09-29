"""Build the synthetic CI warehouse from the committed fixture files.

The fixtures go through the real pipeline code (parse then load), so the
CI dbt build exercises the same path as production, on data that contains
no real record. The first delivery holds one duplicate pair, one partial
date, one bad sex code and one short line on purpose; the second delivery
overlaps it (two republished rows, one corrected row, one late arrival)
so the bitemporal marts are never empty in CI - tests that never catch
anything prove nothing.
"""

from pathlib import Path

from drm import parse, warehouse

FIXTURES = [
    (Path(__file__).parent / "deces-fixture.txt", "fixture-hash"),
    (Path(__file__).parent / "deces-fixture-v2.txt", "fixture-hash-2"),
]
DB_PATH = Path("data/ci_warehouse.duckdb")


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = warehouse.connect(DB_PATH)
    for fixture, file_hash in FIXTURES:
        parquet_path = DB_PATH.parent / f"ci_{file_hash}.parquet"
        quarantine_path = DB_PATH.parent / f"ci_{file_hash}_quarantine.jsonl"
        stats = parse.parse_file(fixture, file_hash, parquet_path, quarantine_path)
        load_stats = warehouse.load_raw(con, parquet_path, file_hash)
        print(
            f"{fixture.name}: {stats['rows']} rows parsed, "
            f"{stats['quarantined']} quarantined, "
            f"{load_stats['inserted']} loaded into {DB_PATH}"
        )


if __name__ == "__main__":
    main()
