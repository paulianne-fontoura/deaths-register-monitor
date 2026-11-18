-- A knowledge-date exception may only move a delivery earlier than the
-- upload date of its url, never later: it records proof that the content
-- was public before the captured version (connaissance_exceptions seed,
-- incident of 2026-11-04). Any row returned is an exception that would
-- delay the knowledge axis, which no evidence can justify.

select
    title,
    file_hash,
    published_at,
    url_published_at
from {{ ref('stg_insee__manifest') }}
where
    published_at_source = 'exception'
    and published_at > url_published_at
