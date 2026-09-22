-- Communes and municipal arrondissements since 1943, one row per code and
-- validity period as published by the INSEE. The 1943 floor is a property
-- of the source: events before 1943 are checked against the earliest known
-- state (rule documented in docs/le-registre.md).

with source as (

    select * from {{ source('cog', 'commune_depuis_1943') }}

),

renamed as (

    select
        com as commune_code,
        typecom as commune_type,
        libelle as commune_label,
        ncc as commune_name_upper,
        cast(date_debut as date) as valid_from,
        cast(date_fin as date) as valid_to
    from source

)

select * from renamed
