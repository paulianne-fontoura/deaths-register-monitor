-- The headline figures computed by BigQuery (ADR-010), twin of
-- dbt/analyses/headline_completeness.sql written in the BigQuery dialect -
-- SAFE_DIVIDE for the ratios, DATE_SUB and CURRENT_DATE() for the
-- 120-day censoring. Both engines must return the same numbers to the
-- digit on the same export.

select
    case
        when mois_deces >= date '2024-10-01'
            then 'observable window (oct 2024+)'
        else 'archive era (2020 - sep 2024)'
    end as era,
    sum(n_deces) as n_deces,
    round(100 * safe_divide(sum(n_connus_30_jours), sum(n_deces)), 2)
        as part_30_jours_pct,
    round(100 * safe_divide(sum(n_connus_90_jours), sum(n_deces)), 2)
        as part_90_jours_pct
from {{ ref('pub_monthly_quality') }}
where
    mois_deces >= date '2020-01-01'
    and mois_deces <= date_sub(current_date(), interval 120 day)
group by era
