-- Versioned country dimension, from the COG countries file since 1943.
-- The register codes foreign birth places with these 99xxx codes.

{{ config(materialized='table') }}

with pays as (

    select
        country_code || '-' || cast(valid_from as varchar) as pays_version_id,
        country_code,
        parent_country_code,
        country_label,
        valid_from,
        valid_to,
        valid_to is null as is_current
    from {{ ref('stg_cog__pays') }}

)

select * from pays
