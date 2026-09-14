# ADR-001 - Entrepôt

Accepté en septembre 2026.

## Contexte

Le registre représente 26 millions de lignes, soit environ 4,6 Go de texte brut réparti en une cinquantaine de fichiers de 5 à 125 Mo, chargés une fois puis complétés d'environ 60 000 lignes par mois. Le projet est mené par une seule développeuse, sans budget, à cadence mensuelle, sur un poste personnel. Les requêtes dominantes sont des balayages colonnaires, triangles, distributions et comparaisons de snapshots. Le projet doit par ailleurs démontrer une portabilité cloud.

## Décision

DuckDB embarqué est l'entrepôt unique de production, sous la forme d'un fichier .duckdb piloté par l'adaptateur dbt-duckdb. BigQuery sandbox est configuré comme second target dbt, à titre de démonstration de portabilité et non d'entrepôt principal.

## Conséquences

L'entrepôt ne demande ni serveur, ni identifiants, ni coût, et se reconstruit depuis la couche brute à tout moment. L'exécution colonnaire absorbe le backfill et les requêtes de triangle sur un laptop, le volume descendant nettement sous 4,6 Go une fois converti en parquet compressé. DuckDB n'accepte qu'un écrivain à la fois, ce qui suffit puisque seul le job mensuel écrit. Il n'offre aucun contrôle d'accès, ce qui reste acceptable parce que l'entrepôt contient du nominatif mais demeure local, seuls des agrégats quittant la machine (ADR-006). Un relecteur du dépôt peut exécuter le pipeline entier sans ouvrir de compte.

## Alternatives écartées

PostgreSQL ajoute une exploitation serveur et un stockage orienté ligne, sans bénéfice pour une charge analytique mono-écrivain. BigQuery en entrepôt principal imposerait les plafonds du bac à sable, des identifiants dans la CI et un compte GCP à tout relecteur. Il est conservé en second target.
