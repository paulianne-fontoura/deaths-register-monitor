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
