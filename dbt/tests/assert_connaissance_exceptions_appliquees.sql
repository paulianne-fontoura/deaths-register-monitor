-- Every knowledge-date exception must match a captured delivery: an
-- exception that matches nothing is a typo in the file hash, and the date
-- it documents is silently not applied. Warn only, and not on the CI
-- fixture warehouse, whose synthetic deliveries carry other hashes.

{{ config(severity='warn', enabled=target.name != 'ci') }}

select exceptions.file_hash
from {{ ref('connaissance_exceptions') }} as exceptions
left join {{ ref('stg_insee__manifest') }} as livraisons
    on exceptions.file_hash = livraisons.file_hash
where livraisons.file_hash is null
