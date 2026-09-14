# Changelog

## [Unreleased]
### Added
- Design document and six architecture decision records (French).
- Initial profiling of three source files (profilage.md).
- Package skeleton with uv, pytest and ruff.
- Pre-commit tooling.
- Ingestion client with data.gouv resource resolution, streaming download and manifest.
- Fixed-width parser to parquet with quarantine and technical columns.
- Continuous integration with GitHub Actions and a README badge.
- DuckDB warehouse: idempotent raw layer keyed on (_file_hash, _row_hash), load log.
- Backfill command covering 1970 to today, resumable, annual over monthly (ADR-004).
- --load option on ingest, chaining download, parse and warehouse load.
