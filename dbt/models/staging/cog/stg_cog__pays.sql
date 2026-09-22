-- Countries and territories since 1943. The register codes foreign birth
-- places with these 99xxx codes.

with source as (

    select * from {{ source('cog', 'pays_et_territoire_depuis_1943') }}

),

renamed as (

    select
        cog as country_code,
        crpay as parent_country_code,
        libcog as country_label,
        cast(date_debut as date) as valid_from,
        cast(date_fin as date) as valid_to
    from source

)

select * from renamed
