-- The completeness triangle: one row per death month and per knowledge
-- point, saying how many deaths of that month the public register held
-- at that date. The knowledge points are the distinct data.gouv upload
-- dates of the manifest (ADR-008); a death enters the triangle at the
-- first delivery that contains it, whatever its delivery. The picture is
-- honest by construction: every death month shows zero until the
-- 2019-12-09 initial drop, and the monthly resolution only begins where
-- monthly deliveries were captured. Rows before the first arrival of a
-- month are omitted.

{{ config(materialized='table') }}

with deces as (

    select
        cast(date_trunc('month', death_date) as date) as mois_deces,
        first_published_at
    from {{ ref('fct_death_records') }}
    where death_date is not null

),

arrivees as (

    select
        mois_deces,
        first_published_at,
        count(*) as n_arrivees
    from deces
    group by mois_deces, first_published_at

),

points_de_connaissance as (

    select distinct published_at
    from {{ ref('stg_insee__manifest') }}

),

cumuls as (

    select
        arrivees.mois_deces,
        points_de_connaissance.published_at,
        cast(sum(arrivees.n_arrivees) as bigint) as n_connus
    from arrivees
    inner join points_de_connaissance
        on arrivees.first_published_at <= points_de_connaissance.published_at
    group by arrivees.mois_deces, points_de_connaissance.published_at

),

totaux as (

    select
        mois_deces,
        cast(sum(n_arrivees) as bigint) as n_total_courant
    from arrivees
    group by mois_deces

),

final as (

    select
        cumuls.mois_deces || '|' || cumuls.published_at as triangle_id,
        cumuls.mois_deces,
        cumuls.published_at,
        datediff('month', cumuls.mois_deces, cumuls.published_at)
            as delai_mois,
        cumuls.n_connus,
        totaux.n_total_courant,
        cumuls.n_connus / cast(totaux.n_total_courant as double)
            as part_connue
    from cumuls
    inner join totaux
        on cumuls.mois_deces = totaux.mois_deces

)

select * from final
