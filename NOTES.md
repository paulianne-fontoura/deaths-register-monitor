# Notes de bord

## 2026-09-12

Profilage initial de trois fichiers en DuckDB. Constats dans profilage.md.

## 2026-09-14

Design doc et six ADR commites. Squelette du paquet drm avec uv, premier test et lint verts. Outillage pre-commit, README v0, modele de PR.

## 2026-09-14 - client d'ingestion

Client d'ingestion livre. Resolution du fichier via l'API data.gouv, telechargement en streaming avec hash SHA-256, manifeste en ajout seul, idempotence verifiee sur le fichier reel du mois d'aout. L'hypothese des 176 caracteres exacts a ete invalidee par le fichier reel, dont les lignes font environ 198 caracteres avec des caracteres non significatifs en fin de ligne, conformes au NOTA du dessin Insee. Regle corrigee, test ajoute.

## 2026-09-14 - parsing vers parquet

Parseur largeur fixe livre. Decoupe des 9 champs du dessin officiel, fallback Latin-1 documente, quarantaine des lignes courtes, colonnes techniques de tracabilite, validation pydantic d'un echantillon de 1000 lignes, ecriture parquet. Cinq tests sur fichiers d'exemple, dont ligne tronquee, encodage casse et date partielle. Fichier d'aout parse en reel, 50 450 lignes, zero quarantaine.

## 2026-09-14 - integration continue

Workflow GitHub Actions livre, lint et tests sur chaque pull request et sur main, via le Makefile. Badge dans le README. Option --parse ajoutee a la commande ingest, make ingest telecharge et produit le parquet en une commande.

## 2026-09-14 - couche brute et backfill

Entrepot DuckDB livre. Table raw_deces alimentee par anti-jointure sur le couple (_file_hash, _row_hash), jamais de suppression, journal load_log, une transaction par fichier. Backfill reel complet, 64 fichiers, 56 annuels 1970-2025 et 8 mensuels 2026, 29 359 940 lignes chargees en 742 secondes, zero echec, le fichier d'aout repris du manifest sans retelechargement. Relance d'idempotence verifiee, 64 fichiers already loaded et zero ligne ajoutee en une seconde. Volumes sur disque, 5,5 Go de brut, 2,7 Go de parquet, 2,4 Go d'entrepot.

## 2026-09-22 - referentiel geographique et orphelins

Etape 8 livree en trois seances. COG millesime 2026 telecharge par drm cog, remplacement en place et historique au manifest. dim_geo versionnee, 43 163 versions pour 39 894 codes depuis 1943, outre-mer inclus, et dim_pays. Regles de deduplication ADR-007 mesurees sur 29 359 940 lignes, 225 505 lignes en trop sur la regle personne, a 2 % de l'ecart connu par ailleurs. Resolution geographique mesuree sur l'entrepot complet, 69 598 lignes sur 29 359 940 non resolues a la date de l'evenement (0,24 %), quatre familles diagnostiquees dans qa_geo_orphelins, codes lieux vides (10 939 deces), codes utilises apres leur fin de validite (54 155), pays en trou de validite, 939 codes jamais publies au COG concentres avant 1988. Exceptions documentees une a une dans la seed geo_exceptions, test singulier en echec sur tout nouveau code inexplique.

## 2026-09-29 - marts bitemporels et reconciliation

Etape 9 livree en quatre seances, contract enforced partout. fct_death_records, 29 133 843 deces canoniques pour 29 359 940 lignes source, 226 097 repliees, 69 deces anterieurs a la naissance gardes sous seuil. Corpus des versions charge via backfill --all-deliveries - data.gouv ne conserve les mensuels que jusqu'a la consolidation annuelle, fenetre reconstituable depuis octobre 2024, argument du monitoring continu. fct_record_versions, 30 190 414 lignes, 1 056 571 versions anciennes, 97 796 deces au contenu modifie entre mensuel et consolidation. Triangle de completude, 38 743 lignes, delai median d'inscription 22 a 39 jours, 16 a 80 pour cent des deces connus a 30 jours, 99 pour cent a 90 jours. Reconciliation contre l'Insee, ecart structurel +0,4 a +1,6 pour cent depuis 1990 (effet de champ, deces a l'etranger inclus au registre), trou de couverture 1997 mesure a -5,6 pour cent et documente en exception, ecart CepiDc +1,6 a +1,8 pour cent stable sur 2019-2024, tests a seuils documentes.

## 2026-09-30 - snapshots des republications et documentation

Etape 10 livree. Snapshot dbt snap_fichiers, etat courant de chaque livraison historise en dimension a evolution lente, une republication ferme la version precedente et en ouvre une nouvelle, mecanique verifiee en simulation avec une republication fabriquee. fct_file_revisions expose les intervalles de validite sous contrat. Documentation complete de tous les modeles (staging, intermediaire, marts, snapshot), site dbt docs genere en local, publication en ligne differee tant que le depot reste prive. Le repertoire snapshots reste hors sqlfluff, son templater jinja ne connait pas la balise snapshot.

## 2026-09-30 - exploitation planifiee

Etape 11 livree. Le projet tourne desormais sans intervention. Sonde hebdomadaire le lundi, drm probe compare les livraisons deces de l'API data.gouv aux url du manifest, une url inconnue est une livraison a capturer (nouveau mensuel ou republication), un titre retire apres consolidation est une information d'audit. Run mensuel le 5, sonde puis controle du pipeline sur fixtures, docs statiques regenerees, artefacts probe-report, manifest et run_results conserves 90 jours. Frontiere nominative actee dans l'ADR-009, aucune donnee reelle en CI, l'entrepot de reference reste sur le poste local, le manifest (metadonnees seules) sort du gitignore et devient l'etat public de la capture. Alertes par issues GitHub dedoublonnees, label capture ferme des que le manifest rattrape, label incident ferme au run mensuel vert suivant, echec simulable par workflow_dispatch. Sonde validee contre l'API reelle le 30 septembre, 79 livraisons listees, 79 capturees, zero en attente apres le backfill du 29.

## 2026-09-30 - fiabilite, runbooks et SLA

Etape 12 livree. Cinq modes de defaillance recenses dans docs/failure-modes.md avec la reaction du systeme pour chacun, quatre runbooks fermes chacun par un exercice date - la panne a ete provoquee, le comportement observe est celui documente. Livraison manquante, sonde sur manifest ampute en bac a sable, 1 livraison a capturer detectee avec sa date. Format modifie, champ renomme dans la fixture, Binder Error lisible, aval saute, rien detruit, fixture restauree. Republication fabriquee dans l'entrepot ci, revision precedente fermee et nouvelle courante a intervalles jointifs. Reconciliation, reference Insee 2015 gonflee de 300 000, echec immediat sur cette seule annee, seed restauree. Engagements chiffres dans docs/sla.md - detection sous 7 jours, capture sous 30 jours, integrite en ajout seul, seuils versionnes, alerte par issue. Les runs planifies appliquent desormais le controle SLA de capture a 30 jours et les issues incident pointent vers failure-modes et les runbooks.
