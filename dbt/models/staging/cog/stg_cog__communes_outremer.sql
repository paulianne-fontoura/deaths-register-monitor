-- Overseas and former-territory communes since 1943, Algeria included.
-- Their codes appear as birth places of older cohorts of the register.

with source as (

    select * from {{ source('cog', 'commune_outremer_depuis_1943') }}

),

renamed as (

    select
        com_comer as commune_code,
        nature_zonage as commune_type,
        libelle as commune_label,
        ncc as commune_name_upper,
        cast(date_debut as date) as valid_from,
        cast(date_fin as date) as valid_to
    from source

)

select * from renamed
