-- Headline figures of the scorecard (etape 13), one row per knowledge
-- era. data.gouv deletes the monthly increments at annual consolidation
-- (ADR-008), so knowledge history is only reconstructable for months
-- whose monthlies survive - October 2024 onward at capture time. In the
-- observable window the shares measure the real registration process;
-- before it they measure what the public archive still allows, which is
-- the quantified case for continuous capture (ADR-009). Months younger
-- than 120 days are excluded - their 90-day share is right-censored.
-- Run with scripts/run_analysis.py after dbt compile.

-- DuckDB analysis; its BigQuery twin is a pub_ model (ADR-010).
{{ config(enabled=target.type == 'duckdb') }}

select
    case
        when mois_deces >= date '2024-10-01'
            then 'observable window (oct 2024+)'
        else 'archive era (2020 - sep 2024)'
    end as era,
    cast(sum(n_deces) as bigint) as n_deces,
    round(sum(n_connus_30_jours) * 100.0 / sum(n_deces), 2)
        as part_30_jours_pct,
    round(sum(n_connus_90_jours) * 100.0 / sum(n_deces), 2)
        as part_90_jours_pct
from {{ ref('fct_monthly_quality') }}
where
    mois_deces >= date '2020-01-01'
    and mois_deces <= current_date - interval 120 day
group by era
order by era
