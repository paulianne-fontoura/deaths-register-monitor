# Modes de défaillance

Ce document recense ce qui peut casser, comment le système le détecte et
ce qu'il fait tout seul. Chaque mode renvoie à un runbook qui dit quoi
faire, et chaque runbook se termine par un exercice daté - la panne a été
provoquée une fois, le comportement observé est celui décrit ici. Les
engagements chiffrés sont dans [sla.md](sla.md).

Principe commun à tous les modes - le système bloque et alerte, il ne
corrige jamais en silence. La couche brute est en ajout seul (ADR-003,
ADR-005), une relance est idempotente, donc aucun incident ne détruit de
données déjà capturées.

| Mode | Exemple | Détection | Réaction du système | Runbook |
|---|---|---|---|---|
| Livraison manquante, en retard, retirée ou remplacée avant capture | Le mensuel de septembre ne paraît pas, ou est remplacé sur place avant capture (4 novembre 2026) | Sonde hebdo et run mensuel (`drm probe`), issue `capture`, contrôle SLA à 7 jours de la première publication, `replaced_before_capture` | Alerte dès la détection, incident au septième jour, version remplacée signalée avec sa date, rien n'est modifié | [01](runbooks/01-livraison-manquante.md) |
| Format modifié | Gabarit de ligne changé, champ renommé dans le manifest, colonne COG disparue | Quarantaine à l'ingestion, Binder Error au staging, contrat dbt au mart | Lignes hors gabarit isolées jamais perdues, build bloqué avec message lisible, aval sauté | [02](runbooks/02-format-modifie.md) |
| Republication silencieuse | Un annuel ré-émis sous le même titre avec un contenu différent | Sonde (url inconnue pour un titre connu), snapshot `snap_fichiers` | Nouvelle révision ouverte, l'ancienne fermée avec son intervalle, versions comparables ligne à ligne | [03](runbooks/03-republication.md) |
| Réconciliation en échec | Le total annuel s'écarte de la série Insee au-delà du seuil | `assert_reconciliation_insee` / `_cepidc` au build | Build en échec, écart lisible dans `qa_reconciliation`, seuils en variables dbt | [04](runbooks/04-reconciliation.md) |
| API data.gouv en panne | La sonde ne peut pas lister le jeu de données | Échec du run planifié | Trois tentatives avec attente exponentielle, puis issue `incident` | [01](runbooks/01-livraison-manquante.md) |

Limites connues et assumées. Un fichier publié puis retiré entre deux
sondes est invisible - la cadence hebdomadaire borne cette fenêtre à sept
jours (ADR-009). Les retraits par consolidation annuelle se jouent à
l'échelle de l'année, mais un remplacement sur place a été observé onze
jours après publication
([post-mortem du 4 novembre 2026](postmortems/2026-11-04-capture-m09.md)) -
d'où le délai de capture de sept jours, qui borne le risque sans l'annuler.
GitHub suspend les crons d'un dépôt inactif soixante jours - le rythme de
commits du projet l'écarte en pratique, et un run manuel les réactive.
