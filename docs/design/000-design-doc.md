# deaths-register-monitor - Document de conception

Version 0.3, septembre 2026. Brouillon, à committer avant tout code de pipeline.

## 1. La question

Combien de temps faut-il pour qu'un décès soit compté, et combien le registre public change-t-il après publication ?

L'Insee publie le fichier des personnes décédées, 26 millions d'enregistrements depuis 1970, mis à jour chaque mois sous Licence Ouverte. Le fichier alimente des travaux de démographie, des contrôles actuariels et des dispositifs de lutte contre la fraude. Il évolue en permanence. Les décès parviennent à l'Insee avec retard, des enregistrements sont corrigés sans documentation, des doublons sont connus, et le producteur indique lui-même ne pas pouvoir garantir l'absence d'omissions ou d'erreurs.

Aucun dispositif ne mesure ces défauts en continu. Les travaux existants se limitent à un nettoyage ponctuel (icem7) et à un moteur de recherche construit au-dessus du fichier (matchID). Le projet fournit un audit de qualité mensuel, automatisé et reproductible, portant sur la complétude du registre, ses délais et son intégrité, avec réconciliation contre les séries statistiques officielles.

## 2. Politique de protection des données

Le dépôt publie du code, de la documentation et des statistiques agrégées. Aucun enregistrement nominatif, même partiel, n'est commité ni publié. Les fichiers bruts restent sur la machine de traitement et sont exclus du contrôle de version dès le premier commit. Les chiffres publiés sont des comptages, des taux et des distributions dont aucun ne permet d'identifier une personne. Le projet ne rediffuse aucun enregistrement. Le mécanisme d'opposition à la rediffusion prévu par l'Insee ne s'applique donc pas à ce dépôt, et son esprit est respecté puisque rien de nominatif ne quitte la machine.

Les données proviennent du fichier des personnes décédées de l'Insee, diffusé sous Licence Ouverte 2.0. Le projet remercie l'Insee pour l'ouverture de ces données.

Le dépôt et toute publication associée s'interdisent le cadrage épidémiologique ou politique, y compris les termes surmortalité, vaccin et Covid. Le projet relève de l'ingénierie de la mesure.

## 3. Le registre, état des connaissances (profilage de septembre 2026)

Le profilage a porté sur trois fichiers, le mensuel d'août 2026, l'annuel 2025 et l'annuel 1970.

1. Les arrivées tardives sont structurelles. 86,0 % des décès du fichier d'août 2026 sont survenus en août, 12,1 % en juillet et 0,9 % en juin. La queue s'étale sur 92 mois distincts et le décès le plus ancien date d'août 1927. Le décompte d'un mois se construit donc sur de nombreuses livraisons.
2. Le fichier annuel 2025 contient 2,2 % de décès d'années antérieures, dont 12 804 de 2024, avec une queue jusqu'à 1935.
3. Un décès du fichier annuel 2025 est daté du 23/12/2026, soit une date postérieure au fichier lui-même.
4. Les dates incomplètes sont codées « 00 ». Le fichier d'août en compte 209 côté naissance et 1 côté décès, l'annuel 2025 en compte 3 302 et 9, l'annuel 1970 en compte 0 et 5.
5. Les doublons exacts apparaissent à la consolidation. Le mensuel n'en contient aucun, l'annuel 2025 en contient 76 paires. Les analyses d'icem7 en documentent environ 221 000 sur l'ensemble du registre.
6. La couverture historique varie. Le fichier 1970 contient 27 006 lignes pour environ 540 000 décès réels, soit 5 % environ, conséquence du début de l'informatisation. La couverture sera documentée fichier par fichier.
7. Le format est un texte à largeur fixe de 176 caractères par enregistrement, conforme au dessin officiel. Les trois fichiers profilés se lisent en UTF-8 sans erreur. Les lignes non conformes seront mises en quarantaine, comptées et publiées comme métrique, jamais corrigées silencieusement.
8. Les codes de lieu suivent le Code Officiel Géographique en vigueur à la date d'enregistrement. Cinquante-sept ans de communes fusionnées ou renommées coexistent donc dans les données, ce qui impose un référentiel COG versionné par millésime (historisation de type SCD2).

## 4. Les trois mesures

### 4.1 Complétude

La mesure repose sur un triangle de développement analogue à ceux de l'actuariat. Les lignes portent le mois de survenue du décès, les colonnes la livraison de publication, et chaque cellule le décompte cumulé des décès du mois M connus après la livraison P. On en déduit des courbes de complétude, c'est-à-dire la part du décompte final d'un mois connue après une, deux ou trois livraisons. Le profilage en donne un exemple direct, 6 100 décès de juillet 2026 figurant encore dans le fichier d'août.

Le décompte final d'un mois est défini comme son décompte à 24 mois de maturité. La queue résiduelle observée au-delà, jusqu'à 92 mois dans le profilage, est mesurée et publiée plutôt qu'ignorée.

### 4.2 Délais

Le délai d'un enregistrement est l'écart entre son mois de livraison et son mois de survenue. Il est publié en distributions (médiane, p90, p99), au niveau national, par département et par période. L'avertissement du producteur sur les délais de transmission des mairies devient ainsi une quantité mesurée.

### 4.3 Intégrité

Trois composantes sont calculées à chaque livraison.

Les doublons, d'abord, sous forme de taux de doublons exacts par fichier, selon la clé définie dans l'ADR-005.

Les corrections, ensuite. L'Insee ne documente aucun mécanisme de correction. Le projet les reconstruit en comparant les livraisons successives qui couvrent une même période, d'une part le fichier annuel N contre les mensuels de l'année N, d'autre part chaque republication d'un fichier contre la version archivée précédente. Les fichiers mensuels sont des incréments et non des photographies du registre, et ne se comparent donc jamais entre eux. Chaque écart est classé comme ajout, modification ou suppression selon la clé d'identité définie dans l'ADR-005. Cette méthodologie n'est documentée nulle part ailleurs et constitue l'apport principal du projet.

La validité, enfin, couvre les décès datés du futur, les dates incomplètes et les codes de lieu inconnus du référentiel COG.

### 4.4 Périmètre temporel des mesures

Chaque mesure n'est calculable que sur la période où la cadence des sources le permet.

| Mesure | Période calculable | Source |
|---|---|---|
| Triangle de complétude et délais | depuis la première année à livraisons mensuelles (à vérifier sur data.gouv, de l'ordre de 2018-2020) | fichiers mensuels |
| Corrections par consolidation annuelle | chaque année close à partir de la même période | annuel contre mensuels |
| Corrections par republication | à partir du premier archivage propre au projet (2026) | snapshots archivés |
| Doublons, validité, couverture | 1970-2026, tout le registre | tous fichiers |

Ce tableau sera précisé lors du backfill. Il borne ce que le projet peut affirmer selon la période.

## 5. Réconciliation

Les décomptes agrégés sont testés contre la série mensuelle de décès de l'Insee (BDM, série 000436394) et contre les comptages annuels du CépiDc-Inserm. Pour les mois à maturité d'au moins 24 livraisons, le décompte du projet doit correspondre à la série officielle à une tolérance près, fixée à 1 % au départ puis ajustée sur pièces. Un test en échec ouvre une note d'investigation. Aucun ajustement silencieux n'est admis. L'implémentation repose sur des tests singuliers dbt exécutés à chaque run du pipeline.

## 6. Architecture et modèle d'exécution

```
data.gouv.fr -> drm ingest (paquet Python, CLI typée, retries, tests)
            -> couche brute (originaux immuables, parquet audité, manifeste)
            -> DuckDB (entrepôt local, fichier unique)
            -> dbt staging (typage, COG normalisé, drapeaux de doublons, quarantaine)
            -> dbt marts (faits bitemporels, dont fct_death_records,
                          fct_record_versions, fct_completeness_triangle,
                          fct_monthly_quality)
            -> scorecard et tableau de bord Power BI
```

Les données nominatives, c'est-à-dire les fichiers bruts et l'entrepôt DuckDB complet, résident exclusivement sur la machine locale (ADR-006). Le cron mensuel GitHub Actions ne manipule que des éléments publiables. Il télécharge la nouvelle livraison depuis data.gouv.fr, la contrôle, met à jour les tables d'agrégats versionnées dans le dépôt (triangle, taux, scorecard) et ouvre une issue en cas d'échec. Le backfill complet et les analyses fines s'exécutent en local. La CI de pull request exécute lint, tests et dbt build sur un échantillon synthétique. BigQuery sandbox est configuré comme second target dbt afin de démontrer la portabilité. Les runbooks et les post-mortems sont tenus dans docs/.

## 7. Hors périmètre

Le projet ne fait pas de nettoyage ponctuel, déjà réalisé par icem7. Il ne fait pas de recherche d'identité ni de rapprochement de personnes, domaine couvert par matchID, et ne fusionne jamais d'identités (ADR-005). Il ne propose aucune interprétation épidémiologique des niveaux ou des tendances mesurés. Il ne vise pas le temps réel, la cadence du registre étant mensuelle.

## 8. Jalons

Fin octobre 2026, première ingestion testée, CI verte, dépôt public. Fin décembre 2026, couches brute et staging complètes, COG versionné, règles de déduplication, marts bitemporels, tests de réconciliation. Mi-mars 2027, cron en production depuis au moins trois mois, scorecard, tableau de bord, README anglais et vidéo de quatre minutes.
