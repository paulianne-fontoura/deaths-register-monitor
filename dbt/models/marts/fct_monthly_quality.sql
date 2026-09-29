-- Quality of the register by death month: registration delays, collapsed
-- duplicate rows and silent corrections, one row per month. The delay of
-- a death is the gap between its date and the first delivery that
-- contains it - for months before the 2019-12-09 initial drop the delay
-- is the age of the public register itself, which is the honest reading.
-- Partial-date records have no month and are measured in qa_doublons.

{{ config(materialized='table') }}

with deces as (

    select
        death_id,
        cast(date_trunc('month', death_date) as date) as mois_deces,
        death_date,
        first_published_at,
        n_source_rows
    from {{ ref('fct_death_records') }}
    where death_date is not null

),

corrections as (

    select distinct death_id
    from {{ ref('fct_record_versions') }}
    where has_corrections

),

final as (

    select
        deces.mois_deces,
        count(*) as n_deces,
        cast(
            median(datediff('day', deces.death_date, deces.first_published_at))
            as bigint
        ) as delai_median_jours,
        count(*) filter (
            where deces.first_published_at <= deces.death_date + interval 30 day
        ) as n_connus_30_jours,
        count(*) filter (
            where deces.first_published_at <= deces.death_date + interval 90 day
        ) as n_connus_90_jours,
        cast(sum(deces.n_source_rows) - count(*) as bigint)
            as n_lignes_repliees,
        count(corrections.death_id) as n_deces_corriges
    from deces
    left join corrections
        on deces.death_id = corrections.death_id
    group by deces.mois_deces

)

select * from final
