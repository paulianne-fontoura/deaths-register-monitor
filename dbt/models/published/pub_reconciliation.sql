-- Yearly reconciliation served from BigQuery (ADR-010). Deliberately not
-- partitioned - 139 rows fit in one block, and partition metadata would
-- cost more than it saves.

select
    annee,
    deces_registre,
    deces_insee,
    ecart_insee_pct,
    champ_insee,
    statut_insee,
    exception_motif,
    deces_cepidc,
    ecart_cepidc_pct,
    _exported_at
from {{ source('exports', 'qa_reconciliation') }}
