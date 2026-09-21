-- One staging model per raw table: english names, light typing, codes kept
-- exactly as published. No filtering, no deduplication (ADR-005).

with source as (

    select * from {{ source('insee', 'raw_deces') }}

),

renamed as (

    select
        -- record as published (fixed-width fields, already trimmed at parsing)
        nom_prenoms as full_name,
        sexe as sex_code,
        date_naissance as birth_date_raw,
        code_lieu_naissance as birth_place_code,
        commune_naissance as birth_commune,
        pays_naissance as birth_country,
        date_deces as death_date_raw,
        code_lieu_deces as death_place_code,
        numero_acte as certificate_number,

        -- typed dates: null when the published value is partial ('00' parts)
        -- or invalid; the raw value above stays available in every case
        cast(try_strptime(date_naissance, '%Y%m%d') as date) as birth_date,
        cast(try_strptime(date_deces, '%Y%m%d') as date) as death_date,

        -- lineage written at parsing time
        _line_number as source_line_number,
        _source_file as source_file,
        _row_hash as row_hash,
        _file_hash as file_hash,
        cast(_ingested_at as timestamp) as ingested_at,

        -- one physical line in one file version: the only safe unique key
        -- of this layer (identical rows inside a file share row_hash)
        _file_hash || '-' || _line_number as record_id

    from source

)

select * from renamed
