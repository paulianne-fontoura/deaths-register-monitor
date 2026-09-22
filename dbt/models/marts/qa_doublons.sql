-- Duplicate measurement of the consolidated register (ADR-007). Loaded
-- snapshots do not overlap in period (annual 1970-2025, monthly 2026), so
-- every group counted here is a real anomaly of the published register,
-- never an artefact of the loading strategy. Count and flag, never merge.

{{ config(materialized='table') }}

with keys as (

    select * from {{ ref('int_deces__person_keys') }}

),

ligne_exacte_meme_fichier as (

    select
        'ligne_exacte_meme_fichier' as regle,
        count(*) as groupes,
        sum(n - 1) as lignes_en_trop
    from (
        select count(*) as n
        from keys
        group by file_hash, row_hash
        having count(*) > 1
    ) as grp

),

ligne_exacte_entre_fichiers as (

    select
        'ligne_exacte_entre_fichiers' as regle,
        count(*) as groupes,
        sum(n - nf) as lignes_en_trop
    from (
        select
            count(*) as n,
            count(distinct file_hash) as nf
        from keys
        group by row_hash
        having count(distinct file_hash) > 1
    ) as grp

),

personne_dates_completes as (

    select
        'personne_dates_completes' as regle,
        count(*) as groupes,
        sum(n - 1) as lignes_en_trop
    from (
        select count(*) as n
        from keys
        where dates_complete
        group by key_person
        having count(*) > 1
    ) as grp

),

evenement as (

    select
        'evenement_date_lieu_acte' as regle,
        count(*) as groupes,
        sum(n - 1) as lignes_en_trop
    from (
        select count(*) as n
        from keys
        group by key_event
        having count(*) > 1
    ) as grp

),

hors_perimetre as (

    select
        'hors_perimetre_dates_partielles' as regle,
        count(*) as groupes,
        cast(null as bigint) as lignes_en_trop
    from keys
    where not dates_complete

),

unioned as (

    select * from ligne_exacte_meme_fichier
    union all
    select * from ligne_exacte_entre_fichiers
    union all
    select * from personne_dates_completes
    union all
    select * from evenement
    union all
    select * from hors_perimetre

)

select * from unioned
