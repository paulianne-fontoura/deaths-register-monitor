-- One row per deduplicated death, current version (ADR-008). The grain
-- and the choice of the current version come from int_deces__canonical;
-- the geographic enrichment resolves the death place in the versioned
-- referential at the event date. Nothing is corrected: the published
-- values stay available raw, the typed columns are null when the source
-- is partial, and the incoherences of the source are flagged, counted
-- and kept under measured thresholds (ADR-008), never silently fixed.

{{ config(materialized='table') }}

with canonical as (

    select
        record_id,
        group_id,
        dates_complete,
        n_source_rows,
        first_published_at,
        last_published_at
    from {{ ref('int_deces__canonical') }}
    where version_rank = 1

),

deces as (

    select * from {{ ref('stg_insee__deces') }}

),

final as (

    select
        canonical.group_id as death_id,
        canonical.record_id,
        deces.full_name,
        deces.sex_code,
        deces.birth_date,
        deces.birth_date_raw,
        deces.birth_place_code,
        deces.birth_commune,
        deces.birth_country,
        deces.death_date,
        deces.death_date_raw,
        deces.death_place_code,
        deces.certificate_number,
        resolution.geo_version_id,
        resolution.pays_version_id,
        coalesce(resolution.statut in ('geo', 'pays'), false) as place_resolue,
        canonical.dates_complete,
        coalesce(deces.death_date >= deces.birth_date, true)
            as dates_coherentes,
        canonical.n_source_rows,
        canonical.first_published_at,
        canonical.last_published_at
    from canonical
    inner join deces
        on canonical.record_id = deces.record_id
    left join {{ ref('int_lieux__resolution') }} as resolution
        on
            deces.death_place_code = resolution.place_code
            and greatest(
                coalesce(deces.death_date, date '1943-01-01'),
                date '1943-01-01'
            ) = resolution.ref_date

)

select * from final
