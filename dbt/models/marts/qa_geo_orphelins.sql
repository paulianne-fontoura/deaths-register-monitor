-- Death place codes that do not resolve in the referential. A code must
-- match dim_geo (communes, arrondissements) or dim_pays (99xxx) at the
-- event date; a missing or partial death date falls back on 1943-01-01,
-- the earliest state the COG publishes (rule in docs/le-registre.md).
-- Unresolved codes are diagnosed, counted and kept visible, never dropped
-- (ADR-005): a blank code is missing data, a code known to the referential
-- but used outside its validity window is a dating anomaly, and a code the
-- COG never published is a coding anomaly. The documented exceptions live
-- in the geo_exceptions seed and the singular test
-- assert_geo_orphelins_documentes fails on any new unexplained code.

{{ config(materialized='table') }}

with deces as (

    select
        death_place_code as place_code,
        greatest(coalesce(death_date, date '1943-01-01'), date '1943-01-01')
            as ref_date,
        death_date is null as date_absente
    from {{ ref('stg_insee__deces') }}

),

deces_par_paire as (

    select
        place_code,
        ref_date,
        date_absente,
        count(*) as n_deces
    from deces
    group by place_code, ref_date, date_absente

),

non_resolues as (

    select
        deces_par_paire.place_code,
        deces_par_paire.ref_date,
        deces_par_paire.date_absente,
        deces_par_paire.n_deces,
        resolution.statut as statut_resolution
    from deces_par_paire
    inner join {{ ref('int_lieux__resolution') }} as resolution
        on
            deces_par_paire.place_code = resolution.place_code
            and deces_par_paire.ref_date = resolution.ref_date
    where resolution.statut in ('orphelin', 'code_absent')

),

codes_geo as (

    select
        commune_code,
        max(commune_label) as libelle
    from {{ ref('dim_geo') }}
    group by commune_code

),

codes_pays as (

    select
        country_code,
        max(country_label) as libelle
    from {{ ref('dim_pays') }}
    group by country_code

),

final as (

    select
        non_resolues.place_code,
        case
            when non_resolues.statut_resolution = 'code_absent'
                then 'code_absent'
            when codes_geo.commune_code is not null
                then 'commune_hors_validite'
            when codes_pays.country_code is not null
                then 'pays_hors_validite'
            else 'hors_referentiel'
        end as statut,
        coalesce(codes_geo.libelle, codes_pays.libelle) as libelle_connu,
        sum(non_resolues.n_deces) as n_deces,
        min(non_resolues.ref_date) as premiere_date_ref,
        max(non_resolues.ref_date) as derniere_date_ref,
        bool_or(non_resolues.date_absente) as date_absente
    from non_resolues
    left join codes_geo
        on non_resolues.place_code = codes_geo.commune_code
    left join codes_pays
        on non_resolues.place_code = codes_pays.country_code
    group by
        non_resolues.place_code,
        non_resolues.statut_resolution,
        codes_geo.commune_code,
        codes_pays.country_code,
        codes_geo.libelle,
        codes_pays.libelle

)

select * from final
