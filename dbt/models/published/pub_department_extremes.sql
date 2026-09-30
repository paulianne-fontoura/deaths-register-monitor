-- Fastest and slowest departments in 2025 on BigQuery (ADR-010), twin of
-- dbt/analyses/department_extremes.sql. QUALIFY filters on the window
-- functions directly; the WHERE clause also prunes the table to the 2025
-- partition. Ties broken on the department code so the ranking is
-- deterministic.

select
    departement,
    n_deces,
    delai_median_jours,
    part_connue_30_jours_pct,
    part_connue_90_jours_pct,
    case
        when row_number() over (
            order by delai_median_jours asc, departement asc
        ) <= 5 then 'fastest'
        else 'slowest'
    end as groupe
from {{ ref('pub_department_quality') }}
where
    annee_deces = 2025
    and departement not in ('etranger', 'inconnu')
    and n_deces >= 500
qualify
    row_number() over (order by delai_median_jours asc, departement asc) <= 5
    or row_number() over (
        order by delai_median_jours desc, departement desc
    ) <= 5
