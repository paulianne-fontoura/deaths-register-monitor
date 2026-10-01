-- Serving layer on BigQuery (ADR-010). Monthly register quality from the
-- published aggregate. Partitioned by an integer month index, not by the
-- date itself - the sandbox expires date partitions 60 days after their
-- boundary, which would erase every historical month on creation, while
-- integer-range partitions never expire. Months before 1960 get a negative
-- index and land in __UNPARTITIONED__. Clustered on the date so date
-- filters still skip blocks. SAFE_DIVIDE returns null on an empty month.

{{ config(
    partition_by={
        'field': 'mois_index',
        'data_type': 'int64',
        'range': {'start': 0, 'end': 1200, 'interval': 1}
    },
    cluster_by=['mois_deces']
) }}

select
    (extract(year from mois_deces) - 1960) * 12
    + extract(month from mois_deces) - 1 as mois_index,
    mois_deces,
    n_deces,
    delai_median_jours,
    n_connus_30_jours,
    n_connus_90_jours,
    safe_divide(n_connus_30_jours, n_deces) as part_connue_30_jours,
    safe_divide(n_connus_90_jours, n_deces) as part_connue_90_jours,
    n_lignes_repliees,
    n_deces_corriges,
    _exported_at
from {{ source('exports', 'fct_monthly_quality') }}
