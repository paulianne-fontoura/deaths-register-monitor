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
- dbt staging layer: sources with freshness, typed staging views, generic tests,
  sqlfluff lint, CI build on a committed synthetic fixture.
- COG referentials: drm cog download with manifest history, versioned dim_geo
  (communes since 1943, overseas included) and dim_pays, synthetic CI fixtures.
- Duplicate rules (ADR-007): name normalization macro, person keys, qa_doublons
  measurement table rebuilt on every dbt build.
- Geographic resolution QA: qa_geo_orphelins diagnosis mart, geo_exceptions
  seed and a singular test failing on any undocumented unresolved place code.
- Bitemporal marts (ADR-008): fct_death_records under an enforced contract,
  two-level canonical grain, real knowledge axis from the manifest urls,
  measured-threshold singular tests.
- Version corpus: backfill --all-deliveries keeps the monthly overlaps,
  is_base flag on deliveries, fct_record_versions (late arrivals and
  corrections) under an enforced contract.
