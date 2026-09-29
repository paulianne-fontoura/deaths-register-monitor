-- Resolution of every (death place code, reference date) pair against the
-- versioned referential: dim_geo for communes, dim_pays for 99xxx codes.
-- The reference date floors at 1943-01-01, the earliest state the COG
-- publishes. Shared by qa_geo_orphelins (diagnosis) and fct_death_records
-- (enrichment), so the interval logic lives in exactly one place.

with paires as (

    select distinct
        death_place_code as place_code,
        greatest(coalesce(death_date, date '1943-01-01'), date '1943-01-01')
            as ref_date
    from {{ ref('stg_insee__deces') }}

),

geo_valide as (

    select
        geo_version_id,
        commune_code,
        valid_from,
        coalesce(valid_to, date '9999-12-31') as valid_to
    from {{ ref('dim_geo') }}

),

pays_valide as (

    select
        pays_version_id,
        country_code,
        valid_from,
        coalesce(valid_to, date '9999-12-31') as valid_to
    from {{ ref('dim_pays') }}

),

resolues as (

    -- adjacent validity intervals share their boundary date, so a pair can
    -- match two versions: min() keeps one deterministically
    select
        paires.place_code,
        paires.ref_date,
        min(geo_valide.geo_version_id) as geo_version_id,
        min(pays_valide.pays_version_id) as pays_version_id
    from paires
    left join geo_valide
        on
            paires.place_code = geo_valide.commune_code
            and paires.ref_date >= geo_valide.valid_from
            and paires.ref_date <= geo_valide.valid_to
    left join pays_valide
        on
            paires.place_code = pays_valide.country_code
            and paires.ref_date >= pays_valide.valid_from
            and paires.ref_date <= pays_valide.valid_to
    group by paires.place_code, paires.ref_date

),

final as (

    select
        place_code,
        ref_date,
        geo_version_id,
        pays_version_id,
        case
            when coalesce(place_code, '') = '' then 'code_absent'
            when geo_version_id is not null then 'geo'
            when pays_version_id is not null then 'pays'
            else 'orphelin'
        end as statut
    from resolues

)

select * from final
