"""Download of the geographic referentials (COG, INSEE).

The register codes places with the Code officiel geographique of the event
year. The COG millesime publishes the full history since 1943 - communes
with validity intervals, overseas and former territories, countries. These
files feed dim_geo and dim_pays.

Referentials are handled differently from the register (ADR-003 applies to
the nominative source only): files are small, public and reproducible, so a
republished file replaces the live one in place, and the manifest keeps the
full download history (name, sha256, date) as the audit trail.
"""

from datetime import UTC, datetime

import httpx

from drm import download, manifest
from drm.config import COG_BASE_URL, Settings

COG_FILES = [
    "v_commune_depuis_1943.csv",
    "v_commune_outremer_depuis_1943.csv",
    "v_tom_depuis_1943.csv",
    "v_pays_et_territoire_depuis_1943.csv",
    "v_mvt_commune_2026.csv",
    "v_commune_2026.csv",
]


def download_cog(client: httpx.Client, settings: Settings) -> list[tuple[str, str]]:
    """Fetch every COG file into the reference layer.

    Returns one (file name, status) pair per file - 'new' when written,
    'unchanged' when the manifest already holds this exact content.
    """
    target_dir = settings.cog_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    results: list[tuple[str, str]] = []
    for name in COG_FILES:
        entries = manifest.load(settings.manifest_path)
        url = COG_BASE_URL + name
        temp_path, sha256, size = download.fetch_to_temp(client, url, target_dir)
        final_path = target_dir / name
        if manifest.seen(entries, name, sha256) and final_path.exists():
            temp_path.unlink()
            results.append((name, "unchanged"))
            continue
        temp_path.replace(final_path)
        manifest.append(
            settings.manifest_path,
            {
                "period": "cog-2026",
                "title": name,
                "url": url,
                "path": str(final_path),
                "sha256": sha256,
                "bytes": size,
                "downloaded_at": datetime.now(UTC).isoformat(timespec="seconds"),
            },
        )
        results.append((name, "new"))
    return results
