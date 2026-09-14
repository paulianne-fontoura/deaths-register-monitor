# ADR-002 - Ingestion

Accepté en septembre 2026.

## Contexte

L'ingestion tourne sans supervision chaque mois. Elle doit survivre aux pannes réseau, être testable sans appeler data.gouv.fr et rester lisible par un relecteur.

## Décision

L'ingestion est portée par un paquet Python nommé drm, décrit par un pyproject et géré avec uv, exposant une CLI typée dont les commandes principales sont `drm ingest deaths --month 2026-08 --dry-run` et `drm backfill --from 1970 --to 2026`. L'outillage retenu comprend typer pour la CLI, pydantic pour la configuration et les modèles d'enregistrement, httpx et tenacity pour les téléchargements avec reprise, pytest et pytest-httpx pour les tests avec HTTP simulé, ruff et pre-commit pour la qualité de code. Les notebooks servent à l'exploration et ne sont jamais sur le chemin du pipeline.

## Conséquences

Chaque comportement d'ingestion est testable unitairement et la CI exécute la suite à chaque pull request. Le mode dry-run rend le cron auditable, le job pouvant annoncer ce qu'il téléchargerait sans le faire. La structure initiale dépasse celle d'un simple script, ce qui est voulu, le paquet faisant partie de la démonstration attendue du projet. Le relecteur dispose d'un point d'entrée unique au lieu d'un dossier de notebooks.
