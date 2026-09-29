-- From 1990 the register coverage has converged and its perimeter is a
-- superset of the Insee one, so the yearly gap must stay positive and
-- under the measured threshold (var seuil_ecart_insee_pct). Earlier
-- years are the measured coverage build-up, documented in NOTES; 1997
-- carries a documented exception in the seed (a measured coverage hole
-- of the register), and any new deviation fails here.

select
    annee,
    deces_registre,
    deces_insee,
    ecart_insee_pct
from {{ ref('qa_reconciliation') }}
where
    annee >= 1990
    and deces_insee is not null
    and coalesce(exception_motif, '') = ''
    and (
        ecart_insee_pct < 0
        or ecart_insee_pct > {{ var('seuil_ecart_insee_pct') }}
    )
