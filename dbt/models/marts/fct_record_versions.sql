-- One row per physical register row, tied to its deduplicated death and
-- its delivery: the bitemporal table (ADR-008). A death whose first
-- delivery is late on the knowledge axis is a late arrival; a death
-- whose content differs between deliveries carries a correction. The
-- table reads every delivery, base and version corpus alike - on the
-- base corpus alone the overlaps barely exist (6 501 rows in two files
-- measured), the content comes with drm backfill deaths
-- --all-deliveries.

{{ config(materialized='table') }}

with versions as (

    select
        group_id as death_id,
        record_id,
        period,
        published_at,
        version_rank,
        version_rank = 1 as is_current
    from {{ ref('int_deces__canonical') }}

),

contenu as (

    select
        record_id,
        file_hash,
        row_hash
    from {{ ref('int_deces__person_keys') }}

),

final as (

    select
        versions.death_id,
        versions.record_id,
        contenu.file_hash,
        contenu.row_hash,
        versions.period,
        versions.published_at,
        versions.version_rank,
        versions.is_current,
        min(contenu.row_hash) over (partition by versions.death_id)
        != max(contenu.row_hash) over (partition by versions.death_id)
            as has_corrections
    from versions
    inner join contenu
        on versions.record_id = contenu.record_id

)

select * from final
