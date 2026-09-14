.RECIPEPREFIX := >
.PHONY: setup lint test ingest

MONTH ?= 2026-08

setup:
> uv sync

lint:
> uv run ruff check .
> uv run ruff format --check .

test:
> uv run pytest

ingest:
> uv run drm ingest deaths --month $(MONTH) --parse
