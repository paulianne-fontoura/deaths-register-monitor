# Runbook 03 - Republication silencieuse

## Symptôme

La sonde liste dans `new_deliveries` un titre déjà présent au manifest,
sous une nouvelle url versionnée - data.gouv a ré-émis le fichier avec
un autre contenu. Ou bien, après capture, le build ouvre une nouvelle
révision dans `snap_fichiers`.

## Diagnostic

`fct_file_revisions` porte le constat - la révision précédente est
fermée (intervalle `valid_from` / `valid_to`), la nouvelle est courante,
et la comparaison de `file_hash`, `bytes` et `lines_in_file` entre les
deux dit l'ampleur du changement. Pour voir le contenu touché,
`fct_record_versions` isole les lignes dont le contenu diffère entre
versions (ADR-008) - c'est la mécanique qui a mesuré 97 796 décès
modifiés entre mensuels et consolidation annuelle.

## Actions

Capturer la nouvelle version par le rituel du runbook 01 - la couche
brute garde les deux versions côte à côte, le snapshot historise, rien à
décider. Si l'ampleur est inhabituelle (un annuel ancien ré-émis, des
milliers de lignes modifiées), mesurer avec `qa_doublons` et
`qa_geo_orphelins` que les chiffres publiés restent invariants, et
documenter l'épisode dans `docs/le-registre.md`.

## Vérification

`fct_file_revisions` montre la révision N fermée et N+1 courante avec
des intervalles jointifs. Les marts qualité sont invariants ou leurs
écarts expliqués.

## Exercice du 30 septembre 2026

Republication fabriquée dans l'entrepôt bac à sable de la CI - une
seconde entrée du même titre `deces-fixture.txt` ajoutée à la fixture
manifest (nouveau hash, nouvelle url, un octet de plus), chaîne snapshot
puis mart relancée. Observé - `deces-fixture.txt-1` fermée,
`deces-fixture.txt-2` courante, intervalles jointifs à la seconde près,
10 PASS. Fixture restaurée. L'entrepôt ci est un bac à sable régénéré à
chaque run - les révisions de l'exercice y restent sans conséquence.
