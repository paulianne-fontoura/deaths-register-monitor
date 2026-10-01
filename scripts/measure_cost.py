"""Measure what the serving layer costs to query on BigQuery (ADR-010).

Runs each query twice - a dry run for the estimate, then for real to read
the bytes processed and billed - and prints a markdown table for
docs/cost.md. Needs the bq dependency group and the DBT_BQ_PROJECT and
DRM_BQ_KEYFILE environment variables. Run from the repository root:

    uv run --group bq python scripts/measure_cost.py
"""

import os

from google.cloud import bigquery
from google.oauth2 import service_account

DATASET = "drm_published"

QUERIES = [
    (
        "triangle, full scan",
        "select * from `{p}.{d}.pub_completeness_triangle`",
    ),
    (
        "triangle, one death month by date (clustering only)",
        (
            "select * from `{p}.{d}.pub_completeness_triangle`"
            " where mois_deces = date '2026-01-01'"
        ),
    ),
    (
        "triangle, one death month by index (partition pruned)",
        (
            "select * from `{p}.{d}.pub_completeness_triangle`"
            " where mois_index = 792"  # (2026 - 1960) * 12, January 2026
        ),
    ),
    (
        "departments, full scan",
        "select * from `{p}.{d}.pub_department_quality`",
    ),
    (
        "departments, 2025 only (integer range pruned)",
        "select * from `{p}.{d}.pub_department_quality` where annee_deces = 2025",
    ),
]


def main() -> None:
    project = os.environ["DBT_BQ_PROJECT"]
    credentials = service_account.Credentials.from_service_account_file(
        os.environ["DRM_BQ_KEYFILE"]
    )
    client = bigquery.Client(project=project, credentials=credentials, location="EU")
    print("| query | estimated (dry run) | processed | billed |")
    print("|---|---:|---:|---:|")
    for label, template in QUERIES:
        sql = template.format(p=project, d=DATASET)
        dry = client.query(
            sql,
            job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False),
        )
        real = client.query(
            sql, job_config=bigquery.QueryJobConfig(use_query_cache=False)
        )
        real.result()
        print(
            f"| {label} | {dry.total_bytes_processed:,} B"
            f" | {real.total_bytes_processed:,} B | {real.total_bytes_billed:,} B |"
        )


if __name__ == "__main__":
    main()
