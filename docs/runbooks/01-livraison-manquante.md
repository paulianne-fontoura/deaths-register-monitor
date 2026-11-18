# Runbook 01 - Livraison manquante, en retard, retirée ou remplacée

## Symptôme

Une issue `capture` est ouverte, ou le mensuel attendu n'apparaît pas
dans la sonde à la mi-mois, ou le run planifié échoue sur « SLA de
capture depasse », ou encore la sonde elle-même échoue (API data.gouv
injoignable après trois tentatives).

## Diagnostic

Lire `probe-report.json` dans l'artefact du run, ou relancer la sonde en
local depuis la racine du dépôt.

    uv run drm probe

Quatre cas se distinguent. Livraison parue mais non capturée -
`new_deliveries` la liste avec sa date de version (`published_at`) et le
début du délai de capture (`pending_since`) ; c'est le cas nominal de
l'alerte. Livraison pas encore parue - rien dans `new_deliveries` ;
l'historique du manifest montre des mises en ligne entre le 3 et le 10 du
mois, un simple décalage se résout seul. Fichier retiré avant capture -
il n'apparaît ni dans `new_deliveries` ni dans le manifest ; c'est une
perte de fenêtre bitemporelle, le cas que la cadence hebdomadaire existe
pour éviter. Version initiale remplacée avant capture -
`replaced_before_capture` vaut `true`, `first_published_at` donne la date
de la première publication ; la version capturée sera la seule connue, et
sa date d'url est postérieure à la date réelle de connaissance du contenu.

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

Version initiale remplacée avant capture - capturer d'abord la version
servie, puis chercher un témoin publié à la date initiale et jamais
modifié depuis, en pratique le trimestriel de la même période. Si le
témoin contient toutes les lignes de la version capturée, ajouter une
ligne à `dbt/seeds/connaissance_exceptions.csv` (empreinte sha256 de la
version capturée, date de première publication, preuve) pour que l'axe de
connaissance date le contenu du jour où il était public. Sans témoin, ne
rien ajouter - la date de l'url reste la seule date démontrable. Dans les
deux cas, consigner la version perdue dans `docs/le-registre.md`.

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

## Incident réel du 4 novembre 2026

Le mensuel de septembre 2026, publié le 5 octobre, a été remplacé sur
place le 16 octobre alors que l'issue `capture` était ouverte depuis onze
jours. La version initiale est perdue, son contenu est prouvé par le
trimestriel t3, et une exception de connaissance date le mensuel du
5 octobre. Le délai de capture est passé de trente à sept jours, compté à
partir de la première publication. Détail dans le
[post-mortem](../postmortems/2026-11-04-capture-m09.md).
