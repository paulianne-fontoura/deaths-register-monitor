with source as (

    select * from {{ source('insee', 'load_log') }}

),

renamed as (

    select
        file_hash,
        source_file,
        rows_in_file,
        rows_inserted,
        seconds as load_seconds,
        cast(loaded_at as timestamp) as loaded_at
    from source

)

select * from renamed
