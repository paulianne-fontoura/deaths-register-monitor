-- Candidate keys for duplicate detection (ADR-007). One row per staging
-- row; nothing is filtered or merged here - keys only. The person key is
-- defined only when both dates are complete, so partial dates can never
-- create false matches.

with base as (

    select
        record_id,
        source_file,
        file_hash,
        row_hash,
        full_name,
        birth_date_raw,
        death_date_raw,
        death_place_code,
        certificate_number,
        birth_date,
        death_date
    from {{ ref('stg_insee__deces') }}

),

keyed as (

    select
        record_id,
        source_file,
        file_hash,
        row_hash,
        {{ normalize_name('full_name') }} as name_normalized,
        birth_date,
        death_date,
        birth_date is not null and death_date is not null as dates_complete,
        case
            when birth_date is not null and death_date is not null
                then
                    {{ normalize_name('full_name') }}
                    || '|' || birth_date_raw
                    || '|' || death_date_raw
        end as key_person,
        death_date_raw
        || '|' || death_place_code
        || '|' || certificate_number as key_event
    from base

)

select * from keyed
