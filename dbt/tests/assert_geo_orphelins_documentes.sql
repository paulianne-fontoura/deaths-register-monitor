-- Every death place code must resolve in the referential at the event
-- date or be a documented exception. The structurally explained families
-- (a code used outside its validity window, a country in a validity gap)
-- are diagnosed by qa_geo_orphelins and stay visible there; this test
-- fails only on a code the COG never published that nobody has documented
-- in the geo_exceptions seed yet. The seed matches with like, so a
-- pattern ('986%') can cover a family when curation justifies it. The CI
-- fixture ends the validity of one commune before a fixture death on
-- purpose, so the mart is never empty in CI.

select
    orphelins.place_code,
    orphelins.n_deces
from {{ ref('qa_geo_orphelins') }} as orphelins
left join {{ ref('geo_exceptions') }} as exceptions
    on orphelins.place_code like exceptions.code_pattern
where
    orphelins.statut = 'hors_referentiel'
    and exceptions.code_pattern is null
