# deaths-register-monitor

![CI](https://github.com/paulianne-fontoura/deaths-register-monitor/actions/workflows/ci.yml/badge.svg)

Continuous quality audit of the French national death register (INSEE "fichier des personnes decedees", 26 million records since 1970).

Every month, the pipeline measures the completeness, delays and integrity of the register, and reconciles the results against official statistical series (INSEE monthly deaths, CepiDc annual counts).

**Status.** Early development. Design document and architecture decision records in [docs/design](docs/design/) (French).

**Data protection.** This repository contains code, documentation and aggregated statistics only. No nominative record is ever committed. Source data by INSEE, Licence Ouverte 2.0.

**Stack.** Python (uv, typer, pydantic, httpx), DuckDB, dbt, GitHub Actions, Power BI.
