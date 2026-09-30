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
- Completeness triangle (fct_completeness_triangle) and monthly quality
  (fct_monthly_quality) under enforced contracts, with a bound-proving
  singular test.
- Reconciliation against the Insee official series and the CepiDc yearly
  counts: sourced seeds, qa_reconciliation under an enforced contract,
  threshold tests with the documented 1997 coverage-hole exception.
- Republication snapshot (snap_fichiers) and fct_file_revisions under an
  enforced contract; complete model documentation, dbt docs generated
  locally (online publication deferred while the repo stays private).
- Scheduled operations (ADR-009): weekly data.gouv probe and monthly run
  with fixture build, static docs and 90-day artifacts; capture and
  incident issues opened, deduplicated and closed automatically, with a
  deliberate-failure input for testing the alert path.
- drm probe command comparing the data.gouv deliveries with the capture
  manifest; the manifest (metadata only) is now tracked in git.
- Reliability pack: failure-mode inventory, four runbooks each closed by a
  dated live drill, and a service-level document (docs/sla.md).
- Capture SLA (30 days) enforced by the scheduled runs; incident issues
  now point at the failure-mode inventory and runbooks.
- Scorecard (etape 13): fct_department_quality aggregate mart under an
  enforced contract, committed analysis queries with a read-only runner,
  BI export script, and an English scorecard (docs/scorecard.md) with a
  committed figure. Headline on the observable window: 99.2% of deaths
  reach the public register within 90 days, 60.2% within 30; the archive
  era shows why continuous capture matters.
- Power BI report as a versioned .pbip project (docs/bi): overview cards,
  archive-cliff curve, completeness-triangle matrix and department
  ranking on the exported aggregates; map visuals are tenant-disabled,
  the ranking replaces them and surfaces the slow consular
  transcriptions (94-day median abroad in 2025).
