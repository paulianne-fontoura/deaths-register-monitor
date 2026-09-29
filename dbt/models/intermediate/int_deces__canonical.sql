-- Canonical grouping of the register rows (ADR-008). Two hierarchical
-- levels: rows sharing the same row_hash are the same published record
-- (level 1, whatever the dates); rows with complete dates sharing the
-- ADR-007 person key are the same person (level 2). Partial-date rows
-- that are not exact copies stay at record grain, and their measured
-- overcount remains visible in qa_doublons. Within each group the
-- current version is the row of the latest delivery on the knowledge
-- axis, tie-broken on the minimal record_id (deterministic, arbitrary,
-- documented in the ADR).

with keyed as (

    select
        record_id,
        file_hash,
        row_hash,
        key_person,
        dates_complete
    from {{ ref('int_deces__person_keys') }}

),

livraisons as (

    select
        file_hash,
        period,
        published_at
    from {{ ref('stg_insee__manifest') }}

),

grouped as (

    select
        keyed.record_id,
        keyed.dates_complete,
        keyed.key_person,
        case
            when keyed.dates_complete then 'p:' || keyed.key_person
            else 'h:' || keyed.row_hash
        end as group_id,
        livraisons.period,
        livraisons.published_at
    from keyed
    inner join livraisons
        on keyed.file_hash = livraisons.file_hash

),

ranked as (

    select
        record_id,
        group_id,
        key_person,
        dates_complete,
        period,
        published_at,
        row_number() over (
            partition by group_id
            order by published_at desc, record_id asc
        ) as version_rank,
        count(*) over (partition by group_id) as n_source_rows,
        min(published_at) over (partition by group_id) as first_published_at,
        max(published_at) over (partition by group_id) as last_published_at
    from grouped

)

select * from ranked
