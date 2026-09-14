\# Notes de bord



\## 2026-09-12

Profilage initial de trois fichiers en DuckDB. Constats dans profilage.md.



\## 2026-09-14

Design doc et six ADR commites. Squelette du paquet drm avec uv, premier test et lint verts. Outillage pre-commit, README v0, modele de PR.



\## 2026-09-14 - client d'ingestion

Client d'ingestion livre. Resolution du fichier via l'API data.gouv, telechargement

en streaming avec hash SHA-256, manifeste en ajout seul, idempotence verifiee sur le

fichier reel du mois d'aout. L'hypothese des 176 caracteres exacts a ete invalidee

par le fichier reel, dont les lignes font environ 198 caracteres avec des caracteres

non significatifs en fin de ligne, conformes au NOTA du dessin Insee. Regle corrigee,

test ajoute.



\## 2026-09-14 - parsing vers parquet

Parseur largeur fixe livre. Decoupe des 9 champs du dessin officiel, fallback

Latin-1 documente, quarantaine des lignes courtes, colonnes techniques de

tracabilite, validation pydantic d'un echantillon de 1000 lignes, ecriture

parquet. Cinq tests sur fichiers d'exemple, dont ligne tronquee, encodage

casse et date partielle. Fichier d'aout parse en reel, 50 450 lignes, zero

quarantaine.
