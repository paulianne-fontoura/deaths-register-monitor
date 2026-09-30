{% snapshot snap_fichiers %}

{{
    config(
        unique_key='title',
        strategy='check',
        check_cols=['file_hash', 'bytes', 'lines_in_file']
    )
}}

-- Current state of every register delivery, one row per file title. A
-- republication changes the content behind the same title (ADR-003: the
-- raw layer keeps every version, the manifest keeps the history); this
-- snapshot historises those changes as a slowly changing dimension, and
-- fct_file_revisions exposes the validity intervals. Run at every dbt
-- build: a run without republication changes nothing. This directory
-- stays outside sqlfluff: its jinja templater does not know the
-- snapshot tag.

with courant as (

    select
        title,
        period,
        delivery_kind,
        file_hash,
        url,
        published_at,
        lines_in_file,
        bytes,
        downloaded_at,
        row_number() over (
            partition by title
            order by downloaded_at desc
        ) as rang
    from {{ ref('stg_insee__manifest') }}

)

select
    title,
    period,
    delivery_kind,
    file_hash,
    url,
    published_at,
    lines_in_file,
    bytes
from courant
where rang = 1

{% endsnapshot %}
