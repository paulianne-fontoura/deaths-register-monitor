-- Register deliveries of the manifest, one row per downloaded file. The
-- upload date embedded in the versioned data.gouv url is the knowledge
-- axis of the bitemporal marts (ADR-008): it says when the public could
-- know. A documented exception can move that date earlier, never later,
-- when another delivery proves the content was public before the version
-- was captured (connaissance_exceptions seed, incident of 2026-11-04).
-- COG referential entries are excluded here. is_base marks the ADR-004
-- corpus (annual files, plus monthlies of years without one): the quality
-- measures read it, while fct_record_versions reads every delivery and
-- treats the overlaps as signal.

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
            as url_published_at,
        lines as lines_in_file,
        bytes,
        cast(downloaded_at as timestamp) as downloaded_at,
        case
            when regexp_matches(period, '^\d{4}$') then 'annual'
            else 'monthly'
        end as delivery_kind,
        left(period, 4) as delivery_year
    from source
    where period not like 'cog%'

),

exceptions as (

    select
        file_hash,
        connu_depuis
    from {{ ref('connaissance_exceptions') }}

),

annees_annuelles as (

    select distinct delivery_year
    from renamed
    where delivery_kind = 'annual'

),

final as (

    select
        renamed.period,
        renamed.title,
        renamed.file_hash,
        renamed.url,
        coalesce(exceptions.connu_depuis, renamed.url_published_at) as published_at,
        renamed.url_published_at,
        case
            when exceptions.connu_depuis is null then 'url' else 'exception'
        end as published_at_source,
        renamed.lines_in_file,
        renamed.bytes,
        renamed.downloaded_at,
        renamed.delivery_kind,
        renamed.delivery_kind = 'annual'
        or annees_annuelles.delivery_year is null as is_base
    from renamed
    left join annees_annuelles
        on renamed.delivery_year = annees_annuelles.delivery_year
    left join exceptions
        on renamed.file_hash = exceptions.file_hash

)

select * from final
