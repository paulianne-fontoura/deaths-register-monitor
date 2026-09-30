# Scorecard - how long does it take to count the dead?

The project's question, answered from the register itself. Every figure
below is an aggregate computed by a committed query on the warehouse -
29,133,843 canonical deaths across the 1970-2026 deliveries - and can be
reproduced with `scripts/run_analysis.py`. No number here derives from a
nominative line, and none is published (project rule).

## Headline

**99.2% of French deaths reach the public register within 90 days of the
death, and 60.2% within 30 days.** Measured on the observable window -
the 1,162,871 deaths of October 2024 through June 2026, the months whose
monthly increments still exist on data.gouv (`headline_completeness`).
The median registration delay moves between 22 and 39 days from month to
month, driven by the publication calendar rather than by the process -
September 2025 was published late and only 16% of its deaths were public
at 30 days, before the month caught up to 99% at 90. A single month
fills in fast - January 2026 was 85.5% known one month out, 98.8% at
two months, complete by September (`knowledge_curve`).

## The archive cliff

![Share of each month's deaths present in the public register](img/completeness-by-month.png)

Before October 2024 the same query returns 1.8% at 30 days and 14.8% at
90. Not because registration was slower - because data.gouv deletes the
monthly files at annual consolidation, and the knowledge history they
carried is gone. What remains of 2020-2024 is one annual file per year,
so only late-year deaths, caught by the January release, look fast. That
asymmetry is the quantified case for the continuous capture this project
runs (ADR-008, ADR-009) - from October 2024 onward the register's real
cadence is preserved and measurable, and it stays measurable only if
every monthly increment keeps being captured before deletion.

## Departments

Metropolitan France is remarkably homogeneous - every department's 2025
median delay falls between 26 and 30 days (`department_extremes`). The
real gaps are overseas - the Pacific collectivities (place codes in 98)
show a 44-day median with 85.7% of deaths known at 90 days, and French
Guiana (973) closes at 98.1%. Registration speed reads as a property of
the national pipeline rather than of local offices - the Power BI report
built on `fct_department_quality` (docs/bi) makes that visible. The
same ranking surfaces one more finding - deaths of French citizens
abroad, transcribed by consulates, reach the register far more
slowly, a 94-day median in 2025 with under half known at 90 days,
consistent with the perimeter gap measured against the Insee series.

## What the register corrects without saying so

Across the whole history, 226,097 source rows fold into canonical deaths
(0.77% of rows), and 97,796 deaths changed content between a monthly
increment and the annual consolidation with no notice - corrections the
bitemporal marts reconstruct (`fct_record_versions`). The annual totals
reconcile with the Insee official series within +0.4 to +1.6% since 1990
(the register includes deaths abroad transcribed into French records),
with one documented coverage hole in 1997 - about 30,000 missing deaths,
-5.6% - kept as a motivated exception (`qa_reconciliation`,
docs/le-registre.md).

## Reproduce it

    uv run dbt compile --project-dir dbt --profiles-dir dbt
    uv run python scripts/run_analysis.py headline_completeness
    uv run python scripts/run_analysis.py department_extremes
    uv run python scripts/run_analysis.py knowledge_curve
    uv run python scripts/export_bi.py
    uv run --with matplotlib python scripts/make_figure.py

Limits - months younger than 120 days are excluded, their 90-day share
being right-censored; the knowledge axis starts at the 2019-12-09
initial drop; delays before October 2024 measure the surviving archive,
not the process. What the pipeline guarantees is in docs/sla.md.
