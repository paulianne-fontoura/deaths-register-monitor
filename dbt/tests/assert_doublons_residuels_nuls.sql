-- fct_death_records must hold zero residual duplicates on the rows
-- eligible to the ADR-007 person rule: by construction every group
-- collapses to its current version, and this test proves it end to end
-- on the published table rather than trusting the construction.

select
    {{ normalize_name('full_name') }}
    || '|' || birth_date_raw
    || '|' || death_date_raw as key_person,
    count(*) as n
from {{ ref('fct_death_records') }}
where dates_complete
group by
    {{ normalize_name('full_name') }}
    || '|' || birth_date_raw
    || '|' || death_date_raw
having count(*) > 1
