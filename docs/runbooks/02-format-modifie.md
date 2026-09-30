# Runbook 02 - Format de fichier modifié

## Symptôme

Le build échoue sur une erreur de colonne au staging (Binder Error), ou
un contrat dbt bloque un mart, ou l'ingestion d'une livraison remonte un
pic anormal de `bad_lines` et de lignes en quarantaine.

## Diagnostic

Identifier la couche qui a bloqué - c'est elle qui dit ce qui a changé.
Ingestion - le gabarit ligne fixe (176 caractères) n'est plus respecté ;
les lignes hors gabarit partent en quarantaine avec leur numéro, rien
n'est perdu, `drm parse` affiche les comptes. Staging - un champ du
manifest ou une colonne d'un fichier COG a été renommé ou supprimé ; le
build s'arrête net avec le nom du champ manquant et saute tout l'aval.
Mart - `contract: enforced` refuse tout écart de schéma ou de type. Dans
tous les cas comparer la livraison au gabarit documenté (`profilage.md`,
`docs/le-registre.md`).

## Actions

Le blocage est le comportement voulu - un ajout de champ est toléré au
staging, une suppression ou un renommage est bloqué par le contrat, et
on ne force jamais. Adapter le code par PR - parseur ou staging selon la
couche, test ajouté qui capture le nouveau format, note dans
`docs/le-registre.md` si le format publié a réellement changé.

## Vérification

`uv run pytest` vert, build ci vert contrats compris, quarantaine
expliquée ligne à ligne.

## Exercice du 30 septembre 2026

Champ `bytes` renommé en `octets` dans la fixture manifest de la CI,
build du staging relancé. Observé - arrêt immédiat sur « Binder Error:
Referenced column "bytes" not found », six modèles aval sautés, aucune
table modifiée. Fixture restaurée par `git checkout`, build relancé -
7 PASS. Comportement conforme - le système bloque avec un message
lisible et ne détruit rien.
