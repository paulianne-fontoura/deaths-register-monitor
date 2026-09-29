-- Reconciliation of the register against the official series, by death
-- year. The register counts the RNIPP registrants, deaths abroad
-- included when transcribed; the Insee series counts deaths occurring
-- in France (France hors Mayotte until 2013, France from 2014); the
-- CepiDc counts residents deceased in France. The three perimeters
-- differ, so the honest expectation is a small stable positive gap
-- against both references once the register coverage converges, not a
-- zero. Gaps are measured here and guarded by the singular tests with
-- documented thresholds and exceptions (reference_deces_insee seed).

{{ config(materialized='table') }}

with registre as (

    select
        cast(year(death_date) as integer) as annee,
        cast(count(*) as bigint) as deces_registre
    from {{ ref('fct_death_records') }}
    where death_date is not null
    group by cast(year(death_date) as integer)

),

insee as (

    select
        annee,
        deces as deces_insee,
        champ as champ_insee,
        statut as statut_insee,
        exception_motif
    from {{ ref('reference_deces_insee') }}

),

cepidc as (

    select
        annee,
        deces as deces_cepidc
    from {{ ref('reference_deces_cepidc') }}

),

final as (

    select
        registre.annee,
        registre.deces_registre,
        insee.deces_insee,
        round(
            100.0 * (registre.deces_registre - insee.deces_insee)
            / insee.deces_insee,
            2
        ) as ecart_insee_pct,
        insee.champ_insee,
        insee.statut_insee,
        insee.exception_motif,
        cepidc.deces_cepidc,
        round(
            100.0 * (registre.deces_registre - cepidc.deces_cepidc)
            / cepidc.deces_cepidc,
            2
        ) as ecart_cepidc_pct
    from registre
    left join insee
        on registre.annee = insee.annee
    left join cepidc
        on registre.annee = cepidc.annee

)

select * from final
