# deaths-register-monitor

![CI](https://github.com/paulianne-fontoura/deaths-register-monitor/actions/workflows/ci.yml/badge.svg)

Continuous quality audit of the French national death register (INSEE "fichier des personnes decedees", 29 million records since 1970).

Every month, the pipeline measures the completeness, delays and integrity of the register, and reconciles the results against official statistical series (INSEE monthly deaths, CepiDc annual counts).

**Status.** Early development. Design document and architecture decision records in [docs/design](docs/design/) (French).

**Raw layer.** Full history loaded on 2026-09-14. 64 files (56 annual 1970-2025, 8 monthly 2026), 29 359 940 rows in DuckDB, 12 minutes end to end, zero failures, 5.5 GB raw, 2.7 GB parquet, 2.4 GB warehouse. Loads insert only unknown (_file_hash, _row_hash) pairs and never delete anything. A second run adds zero rows in one second.

**Data protection.** This repository contains code, documentation and aggregated statistics only. No nominative record is ever committed. Source data by INSEE, Licence Ouverte 2.0.

**Stack.** Python (uv, typer, pydantic, httpx), DuckDB, dbt, GitHub Actions, Power BI.
