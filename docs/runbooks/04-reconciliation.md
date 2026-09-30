# Runbook 04 - Réconciliation en échec

## Symptôme

`assert_reconciliation_insee` ou `assert_reconciliation_cepidc` échoue
au build - le total annuel du registre s'écarte de la référence au-delà
du seuil (2,0 % Insee, 2,5 % CépiDc, années 1990 et suivantes, exceptions
documentées exclues).

## Diagnostic

Lire `qa_reconciliation` pour l'année en cause - décès du registre,
référence, écart en pourcentage. Puis déterminer de quel côté est le
problème. Côté registre - une capture incomplète (vérifier le manifest
et `drm probe`, runbook 01) ou une republication d'ampleur (runbook 03).
Côté référence - l'Insee révise ses séries, un millésime provisoire
(2022-2024 dans la seed) devient définitif avec une autre valeur. Côté
réel - un écart structurel du champ, comme les décès transcrits à
l'étranger inclus au registre (+0,4 à +1,6 % depuis 1990) ou le trou de
couverture 1997, déjà documentés.

## Actions

Capture incomplète - rituel du runbook 01 puis rebuild. Série révisée -
mettre à jour la seed avec la valeur sourcée et son statut par PR, en
citant le fichier Insee ou CépiDc. Écart structurel avéré - le
documenter en exception motivée dans la seed (`exception_motif`, le
précédent est 1997) et dans `docs/le-registre.md`, jamais en relevant le
seuil pour faire passer le build.

## Vérification

Build vert sur `qa_reconciliation` et ses tests, exception ou valeur
révisée tracée dans l'historique git de la seed.

## Exercice du 30 septembre 2026

Référence Insee 2015 gonflée de 300 000 décès dans la seed, chaîne seed
puis mart relancée sur l'entrepôt réel. Observé -
`assert_reconciliation_insee` FAIL avec une ligne, l'année 2015 seule en
cause dans `qa_reconciliation`, écart d'environ un tiers très au-delà du
seuil, message immédiat et lisible. Seed restaurée par `git checkout`,
rebuild - PASS. Comportement conforme - un chiffre de référence faux ne
passe pas inaperçu.
