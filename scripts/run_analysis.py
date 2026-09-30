"""Run a compiled dbt analysis against the local warehouse.

The committed queries live in dbt/analyses/; dbt compile resolves their
refs, and this runner executes the compiled SQL read-only. Usage:

    uv run dbt compile --project-dir dbt --profiles-dir dbt
    uv run python scripts/run_analysis.py headline_completeness
"""

import sys
from pathlib import Path

import duckdb

COMPILED_DIR = Path("dbt/target/compiled/drm/analyses")
WAREHOUSE = Path("data/warehouse.duckdb")


def main() -> None:
    if len(sys.argv) != 2:
        names = sorted(p.stem for p in COMPILED_DIR.glob("*.sql"))
        sys.exit(f"usage: run_analysis.py <name>  (compiled: {', '.join(names)})")
    path = COMPILED_DIR / f"{sys.argv[1]}.sql"
    if not path.exists():
        sys.exit(
            f"{path} not found - run"
            " uv run dbt compile --project-dir dbt --profiles-dir dbt first"
        )
    con = duckdb.connect(str(WAREHOUSE), read_only=True)
    con.sql(path.read_text()).show(max_width=200)


if __name__ == "__main__":
    main()
