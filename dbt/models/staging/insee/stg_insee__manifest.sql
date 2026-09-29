-- Register deliveries of the manifest, one row per downloaded file. The
-- upload date embedded in the versioned data.gouv url is the knowledge
-- axis of the bitemporal marts (ADR-008): it says when the public could
-- know. COG referential entries are excluded here.

with source as (

    select * from {{ source('insee', 'manifest') }}

),

renamed as (

    select
        period,
        title,
        sha256 as file_hash,
        url,
        cast(strptime(regexp_extract(url, '/(\d{8})-\d{6}/', 1), '%Y%m%d') as date)
            as published_at,
        lines as lines_in_file,
        cast(downloaded_at as timestamp) as downloaded_at
    from source
    where period not like 'cog%'

)

select * from renamed
