-- The source contains impossibilities: deaths dated before the birth.
-- Forbidding them would fail forever on a fact of the source (70 rows
-- measured on the full warehouse, ADR-008), so the test guards the
-- measured stock instead: it fails only when the count rises above the
-- documented threshold, which means a new incoherence arrived.

select count(*) as n_incoherences
from {{ ref('fct_death_records') }}
where not dates_coherentes
having count(*) > {{ var('seuil_deces_avant_naissance') }}
