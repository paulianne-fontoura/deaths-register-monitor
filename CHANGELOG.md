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
- BigQuery second target (ADR-010): the same dbt project builds everything
  on DuckDB and only a partitioned serving layer on the BigQuery sandbox;
  drm publish exports allowlisted aggregate marts with a nominative-column
  guard and loads them with load jobs; cost measured by scripts/measure_cost.py.
- README v1 in English: problem, audience, architecture, data model with
  grains, quality checks with their real findings, operations, run
  instructions, decisions and limits.
- make demo (scripts/demo.py): the whole pipeline on the synthetic
  fixtures, offline, ending with what the checks caught.
- MIT licence and a French summary at the top of the README, ahead of the
  repository going public as a reuse of the INSEE register on data.gouv.fr.
- Pre-commit hook refusing absolute user paths in versioned files.

### Fixed
- A fresh clone could not rebuild the raw layer: the versioned manifest
  stores Windows paths, so already-captured deliveries were reported as
  present and then failed to parse. Manifest paths are now read portably,
  and a re-downloaded file with known content is kept where the manifest
  points, without a new manifest line (drm backfill, drm ingest, drm cog).
- dbt source properties moved under config (PropertyMovedToConfigDeprecation).
- pytest collects tests/ only (testpaths), never copies in ignored local folders.
- The Power BI model read its CSV exports from an absolute local path; it now
  reads them through a DossierExports parameter.
- The profiling notes and the design document no longer point at a single
  register record, in line with the aggregates-only rule.
