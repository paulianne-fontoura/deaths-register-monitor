-- Same reconciliation against the CepiDc yearly all-causes counts
-- (residents deceased in France). The register perimeter is wider, so
-- the gap must stay positive and under the measured threshold (var
-- seuil_ecart_cepidc_pct) on the published years.

select
    annee,
    deces_registre,
    deces_cepidc,
    ecart_cepidc_pct
from {{ ref('qa_reconciliation') }}
where
    deces_cepidc is not null
    and (
        ecart_cepidc_pct < 0
        or ecart_cepidc_pct > {{ var('seuil_ecart_cepidc_pct') }}
    )
