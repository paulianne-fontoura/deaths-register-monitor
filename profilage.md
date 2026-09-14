\# Profilage initial - fichier des personnes décédées (Insee)

Séance du 12 septembre 2026. DuckDB 1.5.5, fichiers du 8 septembre 2026.



\## Fichiers analysés

\- deces-2026-m08.txt (mensuel, 9,6 Mo) : 50 450 lignes

\- deces-2025.txt (annuel, 125 Mo) : 659 780 lignes

\- deces-1970.txt (5,2 Mo) : 27 006 lignes



\## Constats

1\. Arrivées tardives (fichier m08) : 86,0 % des décès datent d'août, 12,1 % de juillet,

&#x20;  0,9 % de juin ; 92 mois distincts, le plus ancien : août 1927. La complétude d'un mois

&#x20;  se construit sur plusieurs livraisons -> mesure centrale du projet.

2\. Fichier annuel 2025 : 2,2 % de décès antérieurs à 2025 (dont 12 804 de 2024, queue

&#x20;  jusqu'à 1935).

3\. Anomalie d'intégrité : 1 décès daté du 23/12/2026 dans le fichier annuel 2025 (date

&#x20;  future ; commune 95527, acte n° 47) -> test à implémenter : date\_deces <= date de

&#x20;  publication du fichier.

4\. Dates partielles ("00") : m08 = 209 naissances + 1 décès ; 2025 = 3 302 naissances

&#x20;  + 9 décès ; 1970 = 0 naissance, 5 décès (dont min\_deces = 19700000).

5\. Doublons exacts (nom, naissance, décès, lieu) : 0 dans le mensuel ; annuel 2025 :

&#x20;  76 groupes, 76 lignes en trop (uniquement des paires). Les doublons naissent à la

&#x20;  consolidation annuelle, pas dans les livraisons mensuelles.

6\. Couverture historique : 1970 = 27 006 lignes pour \~540 000 décès réels (\~5 %). Début

&#x20;  de l'informatisation ; la couverture devra être documentée fichier par fichier.

7\. Format : largeur fixe 176 caractères conforme au dessin d'enregistrement ; lecture

&#x20;  UTF-8 sans erreur sur les trois fichiers (pas besoin de latin-1 sur cet échantillon).



\## Conséquences pour le design doc

Complétude par mois de survenue (triangle), délai déclaration/enregistrement, règles de

déduplication à la consolidation, tests d'intégrité (dates futures, dates partielles),

couverture historique par fichier, réconciliation contre la série mensuelle Insee (BDM).

