-- Register quality by department and year on BigQuery (ADR-010). Integer
-- range partitioning on the death year (one partition per year from 1960)
-- and clustering on the department code, the two filters every reading
-- of this table uses. Earlier years land in __UNPARTITIONED__.

{{ config(
    partition_by={
        'field': 'annee_deces',
        'data_type': 'int64',
        'range': {'start': 1960, 'end': 2040, 'interval': 1}
    },
    cluster_by=['departement']
) }}

select
    departement,
    annee_deces,
    n_deces,
    delai_median_jours,
    part_connue_30_jours_pct,
    part_connue_90_jours_pct,
    _exported_at
from {{ source('exports', 'fct_department_quality') }}
