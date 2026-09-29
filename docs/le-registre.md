# Le registre - ce que ce fichier est, et ce qu'il n'est pas

Page de référence du projet. Elle répond à trois questions - qui alimente le
fichier des personnes décédées, ce qu'il contient, ce qu'il ne garantit pas.
Rédigée à partir de la documentation Insee du fichier et des constats mesurés
dans ce dépôt (profilage.md, manifest, entrepôt).

## Qui alimente le fichier

L'état civil des communes enregistre chaque décès et transmet les bulletins à
l'Insee. L'Insee met à jour le Répertoire national d'identification des
personnes physiques (RNIPP) et publie chaque mois, depuis 2019, un extrait
des décès sur data.gouv.fr, sous Licence Ouverte. Les fichiers annuels
remontent à 1970. La publication vise la lutte contre la fraude et la mise à
jour des fichiers clients, pas la statistique - les séries statistiques de
décès de l'Insee et les causes médicales de décès du CépiDc suivent d'autres
circuits, et c'est contre elles que ce projet réconcilie.

## Ce que le fichier contient

Une ligne par personne décédée inscrite au RNIPP, en largeur fixe, neuf
champs - noms et prénoms, sexe, date et lieu de naissance, pays de naissance,
date et lieu de décès, numéro d'acte. Sont donc couverts les décès de
personnes nées en France ou inscrites au répertoire, y compris certains décès
survenus à l'étranger quand ils sont transcrits. Les livraisons se recoupent -
fichiers annuels, mensuels et trimestriels publient les mêmes événements à des
rythmes différents (ADR-004).

## Ce que le fichier ne garantit pas

L'Insee l'écrit dans le descriptif du fichier - il ne peut garantir que le
fichier soit exempt d'erreurs ou d'omissions. Constats mesurés dans ce dépôt,
qui motivent le projet.

- La couverture des premières années est très partielle - le fichier 1970
  contient 27 006 lignes pour environ 540 000 décès cette année-là en France.
  La profondeur "depuis 1970" ne vaut pas exhaustivité depuis 1970.
- Des doublons existent et persistent à la consolidation annuelle. Ils sont
  conservés tels quels dans la couche brute (ADR-005), comptés, jamais
  fusionnés en silence.
- Des dates partielles sont publiées (mois ou jour à 00), et au moins un
  enregistrement daté dans le futur a été observé. Les valeurs publiées sont
  conservées brutes, le typage les met à null sans les corriger.
- L'année 1997 porte un trou de couverture propre au registre - 508 833
  décès contre 539 267 dans la série officielle de l'Insee, soit -5,6 %,
  quand toutes les années 1990-2024 restent entre +0,4 % et +1,6 %.
  L'écart positif structurel est un effet de champ - le registre couvre
  les inscrits au RNIPP, décès transcrits à l'étranger compris, quand la
  série Insee compte les décès survenus en France. La mesure est dans
  qa_reconciliation, gardée par des tests à seuil documenté.
- Les fichiers sont republiés sans journal de modifications. Les corrections
  ne se voient qu'en comparant des livraisons couvrant la même période -
  c'est la mesure centrale du projet (design doc, section 4.3).
- Les lignes portent des caractères non significatifs au-delà de la position
  176, conformes au NOTA du dessin d'enregistrement.
- Les codes lieux suivent le Code officiel géographique de l'année de
  l'événement. Les communes fusionnent et changent de code depuis 1970 -
  la résolution passe par un COG versionné (dim_geo, dim_pays), les
  événements antérieurs à 1943 utilisant l'état le plus ancien publié.
  Mesure sur l'entrepôt complet - 69 598 lignes sur 29 359 940 ne se
  résolvent pas à la date de l'événement (0,24 %). Quatre familles,
  diagnostiquées dans qa_geo_orphelins - des codes lieux vides
  (10 939 décès), des codes utilisés après leur fin de validité
  (renumérotation de la région parisienne de 1968, communes d'Algérie
  après l'indépendance, fusions - 54 155 décès), des pays dans un trou
  de validité (l'Allemagne entre 1949 et 1990), et 939 codes jamais
  publiés au COG, documentés un à un dans la seed geo_exceptions. Les
  codes inconnus se concentrent presque tous entre 1970 et 1987 - la
  codification se stabilise avec l'informatisation du répertoire.

## Ce que le fichier n'est pas

Il ne contient aucune cause de décès - c'est le périmètre du CépiDc. Il ne
remplace pas les séries statistiques officielles. Et un fichier des
oppositions, publié à part, liste les personnes dont les ayants droit
s'opposent à la réutilisation commerciale - toute réutilisation sérieuse le
prend en compte.

## Sources

- Descriptif du fichier et dessin d'enregistrement - data.gouv.fr, jeu
  "Fichier des personnes décédées"
- Code officiel géographique - insee.fr/fr/information/2560452
- COG millésime 2026, fichiers depuis 1943 - insee.fr/fr/information/8740222
- Série officielle des décès - insee.fr/fr/statistiques/8560675 (DEC1,
  France hors Mayotte jusqu'en 2013, France ensuite, 2022-2024 provisoires)
- Effectifs toutes causes - cepidc.inserm.fr, grandes causes de décès
- Constats du dépôt - profilage.md, NOTES.md, tests dbt
