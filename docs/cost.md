# Coût des requêtes sur BigQuery

Mesure du 30 septembre 2026 sur le bac à sable, par
`scripts/measure_cost.py`. Chaque requête est exécutée à blanc (dry run)
puis réellement, cache désactivé. Tables de la couche `pub_` (ADR-010).

| Requête | Estimé à blanc | Traité | Facturé |
|---|---:|---:|---:|
| triangle, balayage complet | 3 370 641 o | 3 370 641 o | 10 485 760 o |
| triangle, un mois filtré par date (regroupement seul) | 3 370 641 o | 696 o | 10 485 760 o |
| triangle, un mois filtré par index (partition élaguée) | 696 o | 696 o | 10 485 760 o |
| départements, balayage complet | 382 790 o | 382 790 o | 10 485 760 o |
| départements, 2025 seule (plage entière élaguée) | 5 526 o | 5 526 o | 10 485 760 o |

## Premier chiffre - l'élagage divise la lecture

Filtrer sur la clé de partition divise les octets lus par environ 4 800
sur le triangle (3,37 Mo ramenés à 696 octets pour un mois de décès) et
par 69 sur la table des départements (383 Ko ramenés à 5,5 Ko pour une
année).

## Deuxième chiffre - la facture ne bouge pas

Les cinq requêtes sont facturées 10 Mio chacune. BigQuery facture un
minimum de 10 Mio par table lue, et toutes ces requêtes restent sous ce
seuil. À ce volume le partitionnement ne change rien au coût, qui reste
de toute façon dans le quota gratuit de 1 Tio de requêtes par mois, soit
environ cent mille requêtes de ce type. Le partitionnement se justifie
ici comme habitude de conception, et par ce qu'il vaudrait sur un vrai
volume - le registre brut, jamais chargé (ADR-009), pèse de l'ordre de
10 Go, qu'un balayage complet facturerait intégralement.

## Le constat le plus utile - l'estimation ne voit pas le regroupement

La requête filtrée par date ne lit elle aussi que 696 octets, alors que
l'estimation à blanc annonçait le balayage complet. Le regroupement
(clustering) élague des blocs à l'exécution, mais l'estimation ne peut
pas le prévoir et renvoie une borne haute. Sur une table regroupée,
l'estimation surestime ; seul le partitionnement rend le coût prévisible
avant d'exécuter. C'est pourquoi l'index de mois est la clé de partition
et la date la clé de regroupement - la partition garantit le coût, le
regroupement aide les requêtes qui filtrent autrement.

## Reproduire

    uv run --group bq python scripts/measure_cost.py

Prérequis - le groupe de dépendances `bq`, les variables
`DBT_BQ_PROJECT` et `DRM_BQ_KEYFILE`, et une couche `pub_` construite
depuis moins de 60 jours (expiration du bac à sable).
