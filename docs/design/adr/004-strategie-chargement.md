# ADR-004 - Stratégie de chargement

Accepté en septembre 2026.

## Contexte

Le backfill couvre 57 ans et 26 millions de lignes sur un poste personnel. Les fichiers se recouvrent. Pour l'année en cours coexistent des fichiers mensuels et trimestriels, dont l'existence a été vérifiée sur data.gouv.fr (deces-2026-m01 à m08, deces-2026-t1 et t2), puis un fichier annuel consolide l'année une fois close. Le profilage montre que cette consolidation ajoute des arrivées tardives et introduit 76 paires de doublons.

Le projet distingue deux axes temporels qu'aucune table ne doit confondre, le temps de l'événement porté par la date du décès et le temps de publication porté par la livraison dans laquelle l'enregistrement apparaît. Chaque table porte les deux axes. C'est le sens donné ici au terme bitemporel.

## Décision

- L'unité de travail est le fichier source. Chaque fichier est chargé en flux dans sa propre transaction et le manifeste le marque comme traité. Un backfill interrompu reprend au fichier suivant et la mémoire reste bornée par le plus gros fichier, environ 125 Mo.
- Le chargement va du plus ancien au plus récent afin que la première apparition de chaque enregistrement soit établie correctement dès le départ.
- La couche brute conserve toutes les sources. En staging, les années closes lisent le fichier annuel et l'année en cours lit les fichiers mensuels.
- Les trimestriels sont ingérés mais exclus des comptages. Leur rôle se limite à un contrôle interne dans lequel un trimestriel doit égaler la somme de ses trois mensuels.
- La date de première apparition d'un enregistrement est celle de la plus ancienne livraison qui le contient, tous types de fichiers confondus.
- La politique de recouvrement est couverte par des tests unitaires dbt et non par convention.

## Conséquences

Le backfill est reprenable, auditable et exécutable sur un poste personnel. Les règles de précédence constituent la logique la plus risquée du projet, d'où le choix de tests explicites plutôt que de conventions. La conservation des trimestriels coûte du stockage et fournit en échange un contrôle de cohérence sans travail supplémentaire.
