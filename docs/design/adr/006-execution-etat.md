# ADR-006 - Exécution et état

Accepté en septembre 2026. Ajouté à la suite de la revue de conception.

## Contexte

Le document de conception prévoit à la fois un cron mensuel GitHub Actions et l'absence de toute donnée nominative hors de la machine locale. Sans décision explicite, ces deux exigences se contredisent, un runner GitHub étant une machine éphémère sur une plateforme publique alors que l'entrepôt complet contient du nominatif.

## Décision

Le projet sépare deux plans d'exécution.

Le backfill, le dossier data/raw/, l'entrepôt DuckDB complet et les analyses fines s'exécutent et résident exclusivement en local, avec la sauvegarde décrite dans l'ADR-003. Rien de cet ensemble n'approche GitHub.

Le cron mensuel GitHub Actions ne manipule que des éléments publiables. Il télécharge la nouvelle livraison depuis data.gouv.fr, la contrôle, recalcule les tables d'agrégats, triangle de complétude, taux de doublons et de quarantaine, scorecard, puis les versionne dans le dépôt. Ces tables sont non nominatives par construction, le job ne persistant aucun enregistrement individuel et le fichier téléchargé disparaissant avec le runner. L'état nécessaire d'un mois sur l'autre, triangle cumulé et manifeste public des livraisons vues, est constitué de ces mêmes agrégats versionnés. En cas d'échec, fichier absent, format modifié ou réconciliation en échec, le job ouvre une issue GitHub avec le contexte.

## Conséquences

L'exigence de protection des données et l'exigence d'automatisation deviennent compatibles et se vérifient à la lecture du workflow. Le tableau de bord public se met à jour chaque mois sans intervention. Les mesures qui exigent l'historique nominatif complet, comme la comparaison fine des snapshots, s'exécutent en local à cadence mensuelle. Si cette limite devenait gênante, l'alternative documentée serait un runner auto-hébergé sur la machine locale, écartée en première version pour sa complexité d'exploitation.
