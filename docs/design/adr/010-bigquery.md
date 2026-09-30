# ADR-010 - BigQuery en seconde cible, agrégats seuls

Statut - accepté. Date - 2026-09-30.

## Contexte

Le projet tourne sur DuckDB, en local, depuis l'étape 6. Une seconde
cible dans un entrepôt cloud démontre que le projet dbt n'est pas lié à
un moteur, et oblige à raisonner en coût, en partitions et en dialecte.
Trois contraintes cadrent le choix. La frontière nominative de l'ADR-009
interdit que le registre quitte le poste local. Le projet ne doit rien
coûter - le bac à sable BigQuery (sandbox) fonctionne sans carte ni
compte de facturation, sur un compte Google personnel. Et ce bac à sable
a ses propres règles - pas de DML ni de streaming, expiration de toute
table après 60 jours, 10 Gio de stockage à vie, non restitués à la
suppression, 1 Tio de requêtes par mois.

## Décision 1 - un projet, deux moteurs, deux rôles

Le même projet dbt porte deux cibles. DuckDB construit tout, depuis les
données nominatives, sur le poste local. BigQuery ne reçoit que les
agrégats publiés et construit une couche de service. La répartition
tient dans `dbt_project.yml` - chaque dossier de modèles, les seeds, les
snapshots et les sources sont activés selon `target.type`, et les
analyses DuckDB portent la même condition. Sur la cible `bq`, dbt ne voit
que les six modèles `pub_` et leurs tests - un `dbt build --target bq`
ne peut pas, par construction, toucher au registre.

## Décision 2 - la frontière est dans le code

`drm publish` n'exporte que quatre marts inscrits sur une liste blanche
(`fct_monthly_quality`, `fct_completeness_triangle`,
`fct_department_quality`, `qa_reconciliation`) et vérifie chaque export
contre une liste noire de colonnes nominatives avant d'écrire quoi que
ce soit. Un mart hors liste ou porteur d'une colonne nominative lève une
erreur, testée. Les exports sont des fichiers parquet chargés par load
jobs en écrasement (`WRITE_TRUNCATE`) - la seule voie d'écriture que le
bac à sable autorise. Le volume publié est de l'ordre de 3 Mo par mois,
soit des décennies avant d'épuiser les 10 Gio à vie. Charger le registre
brut, 29 millions de lignes, épuiserait ce quota et violerait l'ADR-009
dans le même geste.

## Décision 3 - ce que le bac à sable interdit reste en local

Pas de DML, donc pas de snapshot (`MERGE`) ni de modèle incrémental sur
BigQuery - toute la couche `pub_` est matérialisée en tables recréées
par `CREATE OR REPLACE TABLE ... AS SELECT`, ce qui est du DDL. Pas
d'historisation côté cloud - l'historique vit dans l'entrepôt local
(snapshot de l'étape 10, corpus des versions de l'étape 9). L'expiration
à 60 jours devient une contrainte d'exploitation - la source des exports
porte une fraîcheur en alerte à 35 jours et en erreur à 55, avant la
disparition des tables, et la republication mensuelle s'ajoute au rituel
de capture (runbook 01).

## Décision 4 - partitionner par entiers, jamais par dates

Le bac à sable applique aussi une expiration de 60 jours aux partitions,
et pour une table partitionnée sur une colonne de date elle se calcule
depuis la borne de la partition, pas depuis sa création. Partitionner
l'historique par mois de décès effacerait donc, à la création même,
toutes les partitions de plus de deux mois - la table semblerait vide.
Les tables partitionnées par plage d'entiers ne connaissent pas
d'expiration de partition. D'où le choix d'un index de mois entier
(`mois_index`, mois écoulés depuis janvier 1960, partitionné de 0 à 1200
par pas de 1) pour `pub_monthly_quality` et `pub_completeness_triangle`,
regroupées (clustering) par date de décès puis point de connaissance.
Un filtre sur `mois_index` élague les partitions, un filtre sur la date
ne profite que du regroupement - la différence se mesure (décision 5).
`pub_department_quality` est partitionnée par plage entière sur l'année
et regroupée par département, les deux filtres de toute lecture de cette
table. `pub_reconciliation` ne l'est pas - 139 lignes tiennent dans un
bloc, des partitions coûteraient plus en métadonnées qu'elles
n'épargnent. Les mois et années antérieurs à 1960, présents dans le
registre depuis 1882, reçoivent un index négatif et tombent dans la
partition `__UNPARTITIONED__`, lisibles à coût de balayage complet.

## Décision 5 - le coût se mesure, il ne se suppose pas

`scripts/measure_cost.py` exécute chaque requête de référence deux fois,
à blanc (dry run) pour l'estimation puis réellement pour les octets
traités et facturés. Les chiffres sont reportés dans `docs/cost.md`. À
cette échelle la facture est nulle (quota gratuit) et la facturation
minimale de 10 Mo par table lue écrase la différence - le partitionnement
se justifie ici par l'habitude de conception et par ce qu'il vaudrait
sur un volume réel, et les deux colonnes traités / facturés le montrent.

## Décision 6 - deux dialectes, des jumeaux vérifiables

Les deux chiffres-titres existent dans les deux moteurs -
`headline_completeness` et `department_extremes` en analyses DuckDB,
`pub_headline` et `pub_department_extremes` en modèles BigQuery. Ils
doivent rendre les mêmes nombres sur le même export. Les écarts de
dialecte du projet et leur traduction - `SAFE_DIVIDE`, `DATE_SUB`,
`QUALIFY`, les horodatages et les types sont appliqués dans la couche
`pub_`, les autres lignes documentent ce que demanderait le portage
complet des marts -

| DuckDB | BigQuery | Usage dans le projet |
|---|---|---|
| `a / b` (erreur ou infini si b = 0) | `SAFE_DIVIDE(a, b)` renvoie null | parts, chiffre-titre |
| `datediff('day', a, b)` | `DATE_DIFF(b, a, DAY)` - ordre inversé | délais |
| `x + interval 30 day` | `DATE_ADD(x, INTERVAL 30 DAY)` | fenêtres de 30 et 90 jours |
| `current_date - interval 120 day` | `DATE_SUB(CURRENT_DATE(), INTERVAL 120 DAY)` | censure à 120 jours |
| `count(*) filter (where ...)` | `COUNTIF(...)` | décès connus sous k jours |
| `median(x)` | `APPROX_QUANTILES(x, 2)[OFFSET(1)]` (approché) | délai médian |
| `row_number()` puis filtre en CTE | `QUALIFY` (DuckDB l'accepte aussi) | classements |
| `TIMESTAMP` sans fuseau | `TIMESTAMP` = UTC, `DATETIME` = sans fuseau | horodatage d'export |
| `bigint`, `double`, `varchar` | `INT64`, `FLOAT64`, `STRING` | contrats |

Le piège des horodatages est traité à la source - l'export écrit
`_exported_at` en `TIMESTAMP WITH TIME ZONE`, que parquet marque ajusté
UTC et que BigQuery lit en `TIMESTAMP`. Un horodatage sans fuseau serait
lu en `DATETIME` et casserait le contrat. Les modèles `pub_` sont lintés
en dialecte BigQuery (configuration sqlfluff dédiée à leur dossier), le
reste du projet en DuckDB.

## Mesure

Premier chargement réel le 30 septembre 2026. `drm publish` a chargé les
quatre agrégats dans `drm_exports` (1 352 mois, 38 743 cellules du
triangle, 7 329 couples département-année, 139 années), et
`dbt build --target bq` a construit les six tables `pub_` et passé leurs
sept tests. La fraîcheur des quatre sources est au vert. Les jumeaux
concordent au chiffre près - fenêtre observable 1 162 871 décès, 60,19 %
connus sous 30 jours, 99,21 % sous 90, ère archive 3 163 523 décès,
1,84 % et 14,76 %, identiques sur DuckDB et sur BigQuery.

Coût (détail dans `docs/cost.md`) - l'élagage de partition divise la
lecture par environ 4 800 sur le triangle (3,37 Mo ramenés à 696 octets)
et par 69 sur les départements, la facture reste au minimum de 10 Mio
par requête, dans le quota gratuit. Constat inattendu - filtré par date,
le triangle ne lit aussi que 696 octets grâce au regroupement, alors que
l'estimation à blanc annonçait le balayage complet. L'estimation ignore
le regroupement, seule la partition rend le coût prévisible.
