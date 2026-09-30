-- Register quality by death department and year: canonical death count,
-- median delay to first publication and shares known within 30 and 90
-- days. The department comes from the published death place code - DOM
-- codes keep three characters (971-976), a 99xxx code is a death abroad
-- transcribed into the register, an empty code is unknown (measured in
-- qa_geo_orphelins). Codes 91-95 before 1968 can be French Algeria
-- departments, not Ile-de-France - the year keeps that reading honest.
-- Aggregates only, never a nominative line (project rule).

{{ config(materialized='table') }}

with deces as (

    select
        death_date,
        first_published_at,
        case
            when coalesce(death_place_code, '') = '' then 'inconnu'
            when death_place_code like '99%' then 'etranger'
            when death_place_code like '97%'
                then substr(death_place_code, 1, 3)
            else substr(death_place_code, 1, 2)
        end as departement,
        cast(year(death_date) as integer) as annee_deces
    from {{ ref('fct_death_records') }}
    where death_date is not null

),

final as (

    select
        departement,
        annee_deces,
        count(*) as n_deces,
        cast(
            median(datediff('day', death_date, first_published_at))
            as bigint
        ) as delai_median_jours,
        round(
            count(*) filter (
                where first_published_at <= death_date + interval 30 day
            ) * 100.0 / count(*),
            2
        ) as part_connue_30_jours_pct,
        round(
            count(*) filter (
                where first_published_at <= death_date + interval 90 day
            ) * 100.0 / count(*),
            2
        ) as part_connue_90_jours_pct
    from deces
    group by departement, annee_deces

)

select * from final
