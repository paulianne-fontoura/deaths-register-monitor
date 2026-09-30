# Engagements de service

Ce que le projet promet, comment c'est mesuré, et à partir de quand ça
alerte. Les modes de défaillance derrière chaque engagement sont dans
[failure-modes.md](failure-modes.md).

## 1 - Détection

Toute livraison du registre publiée sur data.gouv est détectée sous sept
jours. Mesure - la sonde tourne le lundi (hebdo) et le 5 (run mensuel),
`drm probe` compare les ressources listées aux url du manifest. Alerte -
issue `capture` ouverte dès la détection, avec la liste des livraisons et
leur date de publication.

## 2 - Capture

Toute livraison détectée est capturée localement sous trente jours après
sa publication. Warn - l'issue `capture` reste ouverte tant que le
manifest n'a pas rattrapé. Error - le contrôle SLA du run planifié échoue
au-delà de trente jours et ouvre une issue `incident`. La marge est
d'environ un ordre de grandeur - les retraits observés (mensuels effacés
à la consolidation annuelle) se jouent à l'échelle de l'année.

## 3 - Intégrité

Aucune donnée capturée n'est jamais détruite ni modifiée. La couche
brute est en ajout seul, une version republiée s'ajoute à côté de
l'ancienne, et une relance complète insère zéro ligne (idempotence
mesurée à l'étape 6). Aucun incident, aucun runbook ne comporte d'étape
destructive.

## 4 - Qualité

Le build dbt est vert, contrats compris, ou il échoue visiblement. Les
seuils sont des variables mesurées et versionnées - 70 décès antérieurs
à la naissance (`seuil_deces_avant_naissance`), 2,0 % d'écart à la série
Insee (`seuil_ecart_insee_pct`), 2,5 % au CépiDc
(`seuil_ecart_cepidc_pct`). Tout dépassement casse le build - jamais de
correction silencieuse.

## 5 - Alerte

Un run planifié en échec ouvre une issue `incident` dans les minutes,
avec le lien du run et l'entrée de diagnostic. Le rétablissement ferme
l'issue automatiquement au run mensuel vert suivant. Le circuit a été
testé par un échec volontaire le 30 septembre 2026 (étape 11).

## Limites connues

La fenêtre aveugle de la sonde est de sept jours. Les crons GitHub d'un
dépôt inactif soixante jours sont suspendus. La date de publication est
extraite de l'url versionnée data.gouv - si ce format d'url change, la
sonde le signale comme du neuf à capturer, jamais comme du connu.
