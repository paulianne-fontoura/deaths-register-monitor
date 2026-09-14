.RECIPEPREFIX := >
.PHONY: setup lint test

setup:
> uv sync

lint:
> uv run ruff check .
> uv run ruff format --check .

test:
> uv run pytest
