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

deces_par_code as (

    select
        place_code,
        ref_date,
        date_absente,
        count(*) as n_deces
    from deces
    group by place_code, ref_date, date_absente

),

geo_valide as (

    select
        commune_code,
        valid_from,
        coalesce(valid_to, date '9999-12-31') as valid_to
    from {{ ref('dim_geo') }}

),

pays_valide as (

    select
        country_code,
        valid_from,
        coalesce(valid_to, date '9999-12-31') as valid_to
    from {{ ref('dim_pays') }}

),

resolution as (

    -- adjacent validity intervals share their boundary date, so a code can
    -- match twice: aggregated to one flag per (code, date) group
    select
        deces_par_code.place_code,
        deces_par_code.ref_date,
        deces_par_code.date_absente,
        deces_par_code.n_deces,
        max(case when geo_valide.commune_code is not null then 1 else 0 end)
            as geo_ok,
        max(case when pays_valide.country_code is not null then 1 else 0 end)
            as pays_ok
    from deces_par_code
    left join geo_valide
        on
            deces_par_code.place_code = geo_valide.commune_code
            and deces_par_code.ref_date >= geo_valide.valid_from
            and deces_par_code.ref_date <= geo_valide.valid_to
    left join pays_valide
        on
            deces_par_code.place_code = pays_valide.country_code
            and deces_par_code.ref_date >= pays_valide.valid_from
            and deces_par_code.ref_date <= pays_valide.valid_to
    group by
        deces_par_code.place_code,
        deces_par_code.ref_date,
        deces_par_code.date_absente,
        deces_par_code.n_deces

),

orphelins as (

    select
        place_code,
        ref_date,
        date_absente,
        n_deces
    from resolution
    where geo_ok = 0 and pays_ok = 0

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
        orphelins.place_code,
        case
            when coalesce(orphelins.place_code, '') = '' then 'code_absent'
            when codes_geo.commune_code is not null
                then 'commune_hors_validite'
            when codes_pays.country_code is not null
                then 'pays_hors_validite'
            else 'hors_referentiel'
        end as statut,
        coalesce(codes_geo.libelle, codes_pays.libelle) as libelle_connu,
        sum(orphelins.n_deces) as n_deces,
        min(orphelins.ref_date) as premiere_date_ref,
        max(orphelins.ref_date) as derniere_date_ref,
        bool_or(orphelins.date_absente) as date_absente
    from orphelins
    left join codes_geo
        on orphelins.place_code = codes_geo.commune_code
    left join codes_pays
        on orphelins.place_code = codes_pays.country_code
    group by
        orphelins.place_code,
        codes_geo.commune_code,
        codes_pays.country_code,
        codes_geo.libelle,
        codes_pays.libelle

)

select * from final
