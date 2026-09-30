-- Revision history of the register deliveries, one row per file title
-- and per observed content version. Built on the snap_fichiers snapshot:
-- a file republished with a different content opens a new row and closes
-- the previous one, so the validity interval says when each version was
-- the live one. On a corpus without republication every file has exactly
-- one current revision - the table earns its keep with time, which is
-- the point of the monthly run.

{{ config(materialized='table') }}

with versions as (

    select
        title,
        period,
        delivery_kind,
        file_hash,
        url,
        published_at,
        lines_in_file,
        bytes,
        dbt_valid_from,
        dbt_valid_to,
        dbt_valid_to is null as is_current,
        row_number() over (
            partition by title
            order by dbt_valid_from
        ) as revision_rank
    from {{ ref('snap_fichiers') }}

),

final as (

    select
        title || '-' || cast(revision_rank as varchar) as revision_id,
        title,
        period,
        delivery_kind,
        file_hash,
        url,
        published_at,
        lines_in_file,
        bytes,
        cast(dbt_valid_from as timestamp) as valid_from,
        cast(dbt_valid_to as timestamp) as valid_to,
        is_current,
        cast(revision_rank as bigint) as revision_rank
    from versions

)

select * from final
