"""Run the whole pipeline on the committed synthetic fixtures, offline.

Two small deliveries go through the production code (parse, warehouse
load), then the full dbt project builds on them - staging, referentials,
bitemporal marts, contracts and tests. The fixtures hold deliberate
defects, and the run ends by listing what the checks caught. No real
record is involved. Run from anywhere in the repository:

    make demo
    uv run python scripts/demo.py      (Windows, no make)
"""

import os
import runpy
import shutil
from pathlib import Path

import duckdb
from dbt.cli.main import dbtRunner

ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE = Path("data/ci_warehouse.duckdb")

CAUGHT = [
    (
        "malformed lines quarantined at parse, never loaded",
        "select count(*) from read_json('data/ci_*_quarantine.jsonl')",
    ),
    (
        "rows folded into canonical deaths (duplicates, republications)",
        "select sum(n_source_rows - 1) from fct_death_records",
    ),
    (
        "deaths whose content changed between two deliveries",
        "select count(distinct death_id) from fct_record_versions where has_corrections",
    ),
    (
        "deaths with a partial date (day or month published as 00)",
        "select count(*) from fct_death_records where not dates_complete",
    ),
    (
        "place codes not valid on the event date (versioned COG)",
        "select coalesce(sum(n_deces), 0) from qa_geo_orphelins",
    ),
    (
        "rows with a sex code outside 1 / 2 (the build's one warning)",
        (
            "select count(*) from main_staging.stg_insee__deces"
            " where sex_code is null or sex_code not in ('1', '2')"
        ),
    ),
]


def step(title: str) -> None:
    print(f"\n=== {title}\n", flush=True)


def main() -> None:
    os.chdir(ROOT)

    step("1/4 parse and load two synthetic deliveries")
    runpy.run_path("tests/fixtures/seed_warehouse.py", run_name="__main__")

    step("2/4 load the first delivery again - the raw layer is idempotent")
    from drm import warehouse

    con = warehouse.connect(WAREHOUSE)
    print(
        f"file already loaded, skipped by the CLI: {warehouse.is_loaded(con, 'fixture-hash')}"
    )
    con.close()
    # forced reload on a throwaway copy, so the demo warehouse keeps one
    # load_log line per file (a tested invariant)
    scratch = WAREHOUSE.with_name("ci_idempotence.duckdb")
    shutil.copyfile(WAREHOUSE, scratch)
    con = warehouse.connect(scratch)
    again = warehouse.load_raw(
        con, Path("data/ci_fixture-hash.parquet"), "fixture-hash"
    )
    con.close()
    scratch.unlink()
    print(
        f"forced reload: {again['rows_in_file']} rows in file,"
        f" {again['inserted']} inserted (anti-join on file and row hash)"
    )

    step("3/4 build the dbt project (models, contracts, tests)")
    result = dbtRunner().invoke(
        ["build", "--project-dir", "dbt", "--profiles-dir", "dbt", "--target", "ci"]
    )
    if not result.success:
        raise SystemExit("dbt build failed - see the log above")

    step("4/4 what the checks caught in the synthetic deliveries")
    # same configuration as the connection dbt still holds in this process
    con = duckdb.connect(str(WAREHOUSE))
    for label, sql in CAUGHT:
        print(f"{con.sql(sql).fetchone()[0]:>4}  {label}")
    con.close()
    print(
        "\nEvery defect above was planted in tests/fixtures on purpose -"
        " a check that never fires proves nothing.\n"
        "Same code, same models on the real register - see the README."
    )


if __name__ == "__main__":
    main()
