-- Knowledge accumulation for one death month - how the public count of a
-- given month filled in, knowledge point by knowledge point (the
-- completeness triangle read along one row). January 2026 by default;
-- change the date to read another month. Run with dbt show --inline or
-- any DuckDB client on the compiled code.

select
    mois_deces,
    published_at,
    delai_mois,
    n_connus,
    n_total_courant,
    round(part_connue * 100, 2) as part_connue_pct
from {{ ref('fct_completeness_triangle') }}
where mois_deces = date '2026-01-01'
order by published_at
