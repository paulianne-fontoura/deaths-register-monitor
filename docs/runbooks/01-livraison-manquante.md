# Runbook 01 - Livraison manquante, en retard ou retirée

## Symptôme

Une issue `capture` est ouverte, ou le mensuel attendu n'apparaît pas
dans la sonde à la mi-mois, ou le run planifié échoue sur « SLA de
capture depasse », ou encore la sonde elle-même échoue (API data.gouv
injoignable après trois tentatives).

## Diagnostic

Lire `probe-report.json` dans l'artefact du run, ou relancer la sonde en
local depuis la racine du dépôt.

    uv run drm probe

Trois cas se distinguent. Livraison parue mais non capturée -
`new_deliveries` la liste avec sa date de publication ; c'est le cas
nominal de l'alerte. Livraison pas encore parue - rien dans
`new_deliveries` ; l'historique du manifest montre des mises en ligne
entre le 3 et le 10 du mois, un simple décalage se résout seul. Fichier
retiré avant capture - il n'apparaît ni dans `new_deliveries` ni dans le
manifest ; c'est une perte de fenêtre bitemporelle, le cas que la
cadence hebdomadaire existe pour éviter.

## Actions

Livraison à capturer - dérouler le rituel local puis pousser le manifest.

    uv run drm backfill deaths --all-deliveries
    uv run dbt build --project-dir dbt --profiles-dir dbt
    git add data/manifest.jsonl
    git commit -m "chore: capture <periode>"
    git push

Livraison pas encore parue - aucune action, la sonde suivante tranche.
Fichier retiré non capturé - documenter la perte dans
`docs/le-registre.md` (période, dates de sonde encadrantes) et vérifier
sur data.gouv si une consolidation la couvre. API en panne - l'issue
`incident` reste ouverte, relancer le run à la main quand l'API répond.

## Vérification

`uv run drm probe` affiche `new: 0 to capture`. L'issue `capture` se
ferme automatiquement au run planifié suivant. Rien n'a été modifié ni
supprimé - la capture ajoute, elle n'écrase jamais, et une relance
insère zéro ligne.

## Exercice du 30 septembre 2026

Panne simulée dans un bac à sable, sans toucher au manifest réel - copie
du manifest amputée de l'entrée `deces-2026-m08.txt`, sonde exécutée
depuis ce répertoire. Observé - `captured: 78`, `new: 1 to capture`
avec la date de publication correcte (2026-09-08) et l'indication de la
commande de capture. Contrôle SLA rejoué sur le même rapport - zéro
dépassement à vingt-deux jours de la publication, un dépassement en
antidatant la publication au 1er juillet. Comportement conforme.
