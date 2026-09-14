# ADR-005 - Déduplication et clé d'identité

Accepté en septembre 2026.

## Contexte

Le profilage a trouvé 76 paires de doublons exacts dans le seul fichier annuel 2025. Les analyses d'icem7 en documentent environ 221 000 sur l'ensemble du registre, certains enregistrements étant répétés jusqu'à 40 fois. La résolution d'identité est un métier distinct, couvert par matchID, avec des coûts d'erreur réels. La clé retenue ici sert aussi de clé d'identité pour la comparaison de snapshots décrite au §4.3 du document de conception.

## Décision

La clé de doublon exact réunit nom_prenoms, sexe, date_naissance, code_lieu_naissance, date_deces, code_lieu_deces et numero_acte. Les enregistrements égaux sur la clé complète sont comptés comme doublons et le taux par fichier est une métrique publiée du scorecard.

La clé naturelle utilisée pour la comparaison de snapshots réunit date_deces, code_lieu_deces et numero_acte, le numéro d'acte identifiant l'acte d'état civil dans une commune à une date donnée. Un enregistrement dont la clé naturelle persiste mais dont d'autres champs changent entre deux snapshots est classé comme modifié.

Les quasi-doublons, définis par un même nom, une même date de naissance et une même date de décès avec d'autres champs divergents, sont marqués et comptés sans être résolus. Les marts exposent les décomptes brut et dédupliqué, toujours étiquetés. Le projet n'affirme jamais que deux enregistrements désignent la même personne au-delà de l'égalité exacte de la clé complète, et n'emploie ni rapprochement flou, ni règles phonétiques, ni graphe d'identité.

## Conséquences

Chaque chiffre publié se reproduit depuis une règle énoncée. Le projet sous-compte sciemment les doublons réels par rapport aux approches floues, les 221 000 cas d'icem7 reposant sur des règles citées mais non répliquées, et mesurées sur l'ensemble du registre. Cette limite est documentée. Le positionnement reste celui de la métrologie continue, distinct du nettoyage et de la recherche d'identité.
