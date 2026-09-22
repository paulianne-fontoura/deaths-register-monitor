.RECIPEPREFIX := >
.PHONY: setup lint test ingest backfill cog dbt-build dbt-run dbt-test freshness dbt-ci

MONTH ?= 2026-08
DBT_ARGS = --project-dir dbt --profiles-dir dbt

setup:
> uv sync

lint:
> uv run ruff check .
> uv run ruff format --check .
> uv run sqlfluff lint dbt/models dbt/tests

test:
> uv run pytest

ingest:
> uv run drm ingest deaths --month $(MONTH) --parse

backfill:
> uv run drm backfill deaths

cog:
> uv run drm cog

dbt-build:
> uv run dbt build $(DBT_ARGS)

dbt-run:
> uv run dbt run $(DBT_ARGS)

dbt-test:
> uv run dbt test $(DBT_ARGS)

freshness:
> uv run dbt source freshness $(DBT_ARGS)

dbt-ci:
> uv run python tests/fixtures/seed_warehouse.py
> uv run dbt build $(DBT_ARGS) --target ci
