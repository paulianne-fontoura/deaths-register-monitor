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
| Livraison manquante, en retard ou retirée | Le mensuel de septembre ne paraît pas, ou est retiré avant capture | Sonde hebdo et run mensuel (`drm probe`), issue `capture`, contrôle SLA à 30 jours | Alerte des la détection, incident au dépassement du SLA, rien n'est modifié | [01](runbooks/01-livraison-manquante.md) |
| Format modifié | Gabarit de ligne changé, champ renommé dans le manifest, colonne COG disparue | Quarantaine à l'ingestion, Binder Error au staging, contrat dbt au mart | Lignes hors gabarit isolées jamais perdues, build bloqué avec message lisible, aval sauté | [02](runbooks/02-format-modifie.md) |
| Republication silencieuse | Un annuel ré-émis sous le même titre avec un contenu différent | Sonde (url inconnue pour un titre connu), snapshot `snap_fichiers` | Nouvelle révision ouverte, l'ancienne fermée avec son intervalle, versions comparables ligne à ligne | [03](runbooks/03-republication.md) |
| Réconciliation en échec | Le total annuel s'écarte de la série Insee au-delà du seuil | `assert_reconciliation_insee` / `_cepidc` au build | Build en échec, écart lisible dans `qa_reconciliation`, seuils en variables dbt | [04](runbooks/04-reconciliation.md) |
| API data.gouv en panne | La sonde ne peut pas lister le jeu de données | Échec du run planifié | Trois tentatives avec attente exponentielle, puis issue `incident` | [01](runbooks/01-livraison-manquante.md) |

Limites connues et assumées. Un fichier publié puis retiré entre deux
sondes est invisible - la cadence hebdomadaire borne cette fenêtre à sept
jours, contre des retraits observés à l'échelle de l'année (ADR-009).
GitHub suspend les crons d'un dépôt inactif soixante jours - le rythme de
commits du projet l'écarte en pratique, et un run manuel les réactive.
