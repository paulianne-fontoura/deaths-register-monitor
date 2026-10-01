-- The completeness triangle served from BigQuery (ADR-010). Same integer
-- month index partitioning as pub_monthly_quality (date partitions would
-- expire on creation in the sandbox), clustered by death month then
-- knowledge point - reading one month's knowledge curve by its index
-- scans one partition, not the 38,000-row table.

{{ config(
    partition_by={
        'field': 'mois_index',
        'data_type': 'int64',
        'range': {'start': 0, 'end': 1200, 'interval': 1}
    },
    cluster_by=['mois_deces', 'published_at']
) }}

select
    (extract(year from mois_deces) - 1960) * 12
    + extract(month from mois_deces) - 1 as mois_index,
    triangle_id,
    mois_deces,
    published_at,
    delai_mois,
    n_connus,
    n_total_courant,
    part_connue,
    _exported_at
from {{ source('exports', 'fct_completeness_triangle') }}
