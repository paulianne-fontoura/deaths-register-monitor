# ADR-003 - Couche brute

Accepté en septembre 2026.

## Contexte

L'Insee republie et corrige des fichiers sans documentation. La mesure des corrections décrite au §4.3 du document de conception suppose de conserver chaque version telle qu'elle a été téléchargée, à sa date de téléchargement. Les versions passées d'un fichier républié sont irremplaçables, aucune source ne permettant de les retrouver une fois écrasées chez le producteur. Les réexécutions du pipeline ne doivent jamais dupliquer de données.

## Décision

- Les originaux sont stockés tels que téléchargés sous data/raw/, hors git dès le premier commit, et décrits dans un manifeste qui enregistre l'URL source, l'horodatage de téléchargement, le SHA-256, la taille et la période couverte.
- Chaque original est parsé à l'identique vers parquet par découpe à largeur fixe, sans aucun nettoyage, avec load_id, source_file et line_number.
- Les lignes non conformes partent dans une table de quarantaine avec leur motif. Elles sont comptées dans le scorecard et jamais corrigées silencieusement.
- Le chargement est idempotent. Un fichier déjà vu, identifié par sa période et son SHA-256, est ignoré. Un nouveau hash sur une même période crée une nouvelle version de snapshot sans écrasement. La couche brute est en ajout seul.
- Après chaque livraison, data/raw/ et le manifeste sont copiés vers un second support, disque externe ou stockage cloud privé. Le code est quant à lui protégé par git.

## Conséquences

Les snapshots successifs d'une même période deviennent comparables, ce qui rend la mesure des corrections possible. Toute table aval peut être supprimée et reconstruite depuis le brut, et le brut se réaudite depuis le manifeste. Le stockage croît d'environ 10 Mo par mois, ce qui reste acceptable sur un poste personnel pendant plusieurs années. Le contrôle de hash rend les réexécutions accidentelles sans effet.
