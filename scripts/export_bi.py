"""Export the aggregate marts to CSV for Power BI (etape 13).

Reads the local warehouse and writes one CSV per aggregate mart into
data/exports/, outside git. Aggregates only - no mart exported here
carries a nominative line (project rule), the BI layer never sees the
register itself. Run from the repository root:

    uv run python scripts/export_bi.py
"""

from pathlib import Path

import duckdb

MARTS = [
    "fct_completeness_triangle",
    "fct_monthly_quality",
    "fct_department_quality",
    "qa_reconciliation",
]

WAREHOUSE = Path("data/warehouse.duckdb")
EXPORT_DIR = Path("data/exports")


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(WAREHOUSE), read_only=True)
    for mart in MARTS:
        schema = con.sql(
            "select table_schema from information_schema.tables where table_name = ?",
            params=[mart],
        ).fetchone()
        if schema is None:
            print(f"{mart}: not found in the warehouse, run dbt build first")
            continue
        target = EXPORT_DIR / f"{mart}.csv"
        con.sql(
            f"copy (select * from {schema[0]}.{mart})"
            f" to '{target}' (header, delimiter ',')"
        )
        rows = con.sql(f"select count(*) from {schema[0]}.{mart}").fetchone()[0]
        print(f"{mart}: {rows} rows -> {target}")


if __name__ == "__main__":
    main()
