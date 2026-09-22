# ADR-007 - Règles de déduplication

Statut - accepté. Date - 22 septembre 2026.

## Contexte

Le registre contient des doublons et les conserve d'une livraison à l'autre.
L'ADR-005 a fixé la ligne de conduite de la couche brute - compter et
marquer, jamais fusionner. Le présent ADR définit ce qui compte comme
doublon, avec quels champs, quelle normalisation et quelles tolérances, et
comment le taux est mesuré. Les instantanés chargés ne se recouvrent pas en
période (annuels 1970-2025, mensuels 2026, ADR-004) - tout groupe détecté
est donc une anomalie du registre publié, jamais un artefact du chargement.

## Décision

Trois règles hiérarchisées, plus un indicateur.

- Ligne exacte, même fichier. Deux lignes physiquement identiques dans la
  même livraison (même file_hash, même row_hash). Le doublon le plus sûr.
- Ligne exacte, entre fichiers. La même ligne publiée dans deux livraisons
  de périodes différentes - un enregistrement compté deux fois, par exemple
  déclaré en fin d'année puis republié dans un mensuel suivant.
- Personne normalisée, dates complètes. Même nom normalisé, même date de
  naissance, même date de décès. La règle ne s'applique qu'aux lignes dont
  les deux dates sont complètes - une date partielle ne peut jamais créer
  de correspondance. Les lignes à dates partielles sont comptées à part,
  hors périmètre.
- Indicateur événement. Même date de décès, même lieu, même numéro d'acte.
  Un numéro d'acte est censé être unique par commune et par année - les
  collisions signalent soit un doublon, soit une réutilisation de numéro à
  documenter. Indicateur d'anomalie, pas règle de suppression.

Normalisation des noms, exacte et sans exception - majuscules, accents
supprimés, tout caractère non alphabétique remplacé par une espace, espaces
consécutives réduites, bords nettoyés. Aucune correspondance floue en
version 1 - la distance d'édition rapprocherait des homonymes et le coût
d'un faux positif dépasse celui d'un faux négatif dans un audit.

La mesure est matérialisée dans la table qa_doublons, reconstruite à chaque
dbt build - une ligne par règle, nombre de groupes et de lignes en trop.
Aucun rapprochement n'entraîne de fusion ni de suppression.

## Mesure

Pilote sur le seul fichier 1970 (27 006 lignes) - zéro ligne exacte
dupliquée, zéro personne dupliquée, 31 groupes de collision d'acte
(71 lignes), 5 lignes à dates partielles.

Mesure complète du 22 septembre 2026, entrepôt consolidé de
29 359 940 lignes.

- Ligne exacte, même fichier - 114 047 groupes, 120 678 lignes en trop.
- Ligne exacte, entre fichiers - 6 503 lignes publiées dans plus d'une
  livraison de périodes différentes, 221 lignes en trop au-delà d'une
  par fichier.
- Personne normalisée, dates complètes - 210 694 groupes, 225 505 lignes
  en trop.
- Indicateur événement - 218 268 collisions de date, lieu et numéro d'acte,
  236 226 lignes en trop.
- Hors périmètre, dates partielles - 115 832 lignes.

La préparation du projet mentionnait environ 221 000 doublons connus de
sources externes. Notre règle personne en mesure 225 505 - convergence à
2 % près avec une définition indépendante, l'écart s'expliquant par des
règles et des périmètres différents. Le pilote 1970 était trompeur par
excès de propreté - les doublons se concentrent dans d'autres millésimes.

## Conséquences

- Les chiffres mesurés sont publiés dans le README et les notes de bord.
- Les homonymes complets nés et décédés les mêmes jours restent un risque
  résiduel assumé de la règle personne - documenté, non corrigé.
- Toute évolution des règles passe par une révision de cet ADR.
