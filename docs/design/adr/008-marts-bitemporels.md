# ADR-008 - Marts bitemporels, grain canonique et seuils

Statut - accepté. Date - 2026-09-22.

## Contexte

Les couches précédentes conservent tout (ADR-005) et mesurent les doublons
sans les fusionner (ADR-007). L'étape 9 construit les tables d'analyse. Il
faut donc décider ce qu'est « un décès » dans un mart, comment choisir la
version courante d'un enregistrement publié plusieurs fois, et sur quels
axes temporels raisonner.

## Décision 1 - deux axes temporels, tous deux réels

L'axe de validité est la date de l'événement (date de décès publiée).
L'axe de connaissance est la date de mise en ligne de la livraison sur
data.gouv, extraite de l'URL versionnée conservée au manifest
(`.../20191209-182920/deces-1970.txt`). Cette date est vérifiée présente
pour les 64 livraisons chargées. Elle dit quand le public pouvait savoir,
ce qui est la question du projet.

Conséquence mesurée - l'histoire 1970-2018 (49 fichiers) est mise en ligne
en une seule fois le 9 décembre 2019. Avant cette date, le registre public
n'existe pas. Les fichiers annuels suivants arrivent une fois par an, les
mensuels au début du mois suivant. La granularité mensuelle de l'axe de
connaissance ne commence donc qu'avec les livraisons mensuelles.

## Décision 2 - grain canonique de fct_death_records

Une ligne par décès dédupliqué, en deux niveaux hiérarchisés.

Niveau 1, identité exacte - les lignes qui partagent le même `_row_hash`
sont le même enregistrement publié plusieurs fois. Elles forment un seul
groupe, quel que soit l'état des dates.

Niveau 2, identité personne - les lignes à dates complètes qui partagent
la clé personne d'ADR-007 (nom normalisé, date de naissance, date de
décès) forment un seul groupe.

Les lignes à dates partielles qui ne sont pas des copies exactes restent
au grain enregistrement. Le surcompte qui en résulte est celui mesuré en
ADR-007 (115 832 lignes hors périmètre de la règle personne) et reste
visible dans qa_doublons.

## Décision 3 - version courante

Dans chaque groupe, la version courante est la ligne de la livraison la
plus récente sur l'axe de connaissance (les corrections remplacent les
versions antérieures). À égalité, le `record_id` minimal, choix arbitraire
mais déterministe, documenté ici.

## Décision 4 - cohérences en seuils mesurés, pas en interdits

La source contient des impossibilités. Mesure sur l'entrepôt complet -
70 décès antérieurs à la date de naissance sur 29 244 108 paires de dates
typables. Un test qui interdirait ces lignes échouerait pour toujours sur
un fait de la source. Les tests singuliers vérifient donc que les stocks
d'incohérences restent sous un seuil fixé à la valeur mesurée, portée en
variable dbt. Le dépassement du seuil signale une nouveauté à examiner,
pas le stock connu.

Seuils fixés à la mesure du 22 septembre 2026 -
`seuil_deces_avant_naissance` 70. Les doublons résiduels de
fct_death_records sur les lignes éligibles à la règle personne doivent
être nuls par construction, et le test le prouve à zéro, sans seuil.

## Décision 5 - contrats

Les marts de l'étape 9 portent `contract: enforced`. Le schéma publié est
un engagement, pas un effet de bord du SQL.

## Mesure du 29 septembre 2026

Première construction de fct_death_records sur l'entrepôt complet -
29 133 843 enregistrements canoniques pour 29 359 940 lignes source,
soit 226 097 lignes repliées en 211 245 groupes, cohérent avec la
mesure d'ADR-007. Après déduplication, 69 décès antérieurs à la
naissance subsistent sous le seuil de 70 (une paire du stock mesuré
était elle-même un doublon), 99,8 % des lieux de décès sont résolus
dans le référentiel versionné et 99,6 % des enregistrements portent
deux dates complètes.

## Conséquences

fct_death_records repose sur trois intermédiaires - les clés d'ADR-007,
la résolution géographique par intervalle (partagée avec qa_geo_orphelins)
et le manifest en staging pour l'axe de connaissance. fct_record_versions
(une ligne par enregistrement et par livraison) n'a de contenu réel
qu'avec les livraisons qui se recouvrent - la mesure montre 6 501 lignes
présentes dans deux fichiers et 2 dans trois avec le corpus actuel, chargé
sous la préséance annuelle d'ADR-004. Le chargement des livraisons
mensuelles historiques pour l'axe bitemporel est traité en séance B.
