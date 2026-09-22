-- Versioned geographic dimension. One row per place code and validity
-- period, covering communes and municipal arrondissements since 1943,
-- overseas and former territories included. Nothing is invented - the
-- intervals are the ones the INSEE publishes; departement and region are
-- added for current codes only.

{{ config(materialized='table') }}

with communes as (

    select
        commune_code,
        commune_type,
        commune_label,
        commune_name_upper,
        valid_from,
        valid_to,
        'metropole_dom' as scope
    from {{ ref('stg_cog__communes') }}

),

outremer as (

    select
        commune_code,
        commune_type,
        commune_label,
        commune_name_upper,
        valid_from,
        valid_to,
        'outremer_historique' as scope
    from {{ ref('stg_cog__communes_outremer') }}

),

unioned as (

    select * from communes
    union all
    select * from outremer

),

current_millesime as (

    -- Only communes and municipal arrondissements: communes deleguees and
    -- associees share the code of another row and would fan out the join.
    select
        com as commune_code,
        dep as departement_code,
        reg as region_code
    from {{ source('cog', 'commune_2026') }}
    where typecom in ('COM', 'ARM')

),

final as (

    select
        unioned.commune_code || '-' || cast(unioned.valid_from as varchar)
            as geo_version_id,
        unioned.commune_code,
        unioned.commune_type,
        unioned.commune_label,
        unioned.commune_name_upper,
        unioned.scope,
        unioned.valid_from,
        unioned.valid_to,
        unioned.valid_to is null as is_current,
        current_millesime.departement_code,
        current_millesime.region_code
    from unioned
    left join current_millesime
        on
            unioned.commune_code = current_millesime.commune_code
            and unioned.valid_to is null

)

select * from final
