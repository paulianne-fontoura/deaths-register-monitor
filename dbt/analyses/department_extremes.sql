-- Departments with the fastest and slowest registration, death year 2025
-- - the latest complete year fully inside the observable knowledge
-- window (monthly increments survive from October 2024, see
-- headline_completeness). Small departments below 500 deaths and the
-- etranger / inconnu buckets are excluded so the ranking compares
-- comparable processes. Run with scripts/run_analysis.py.

-- DuckDB analysis; its BigQuery twin is a pub_ model (ADR-010).
{{ config(enabled=target.type == 'duckdb') }}

with classement as (

    select
        departement,
        n_deces,
        delai_median_jours,
        part_connue_30_jours_pct,
        part_connue_90_jours_pct,
        row_number() over (order by delai_median_jours asc) as rang_rapide,
        row_number() over (order by delai_median_jours desc) as rang_lent
    from {{ ref('fct_department_quality') }}
    where
        annee_deces = 2025
        and departement not in ('etranger', 'inconnu')
        and n_deces >= 500

)

select
    departement,
    n_deces,
    delai_median_jours,
    part_connue_30_jours_pct,
    part_connue_90_jours_pct,
    case when rang_rapide <= 5 then 'fastest' else 'slowest' end as groupe
from classement
where rang_rapide <= 5 or rang_lent <= 5
order by delai_median_jours
