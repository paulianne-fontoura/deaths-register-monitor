"""Project settings and constants."""

from pathlib import Path

from pydantic import BaseModel

DATASET_API = "https://www.data.gouv.fr/api/1/datasets/fichier-des-personnes-decedees/"
RECORD_LENGTH = 176

# COG millesime page: insee.fr/fr/information/8740222 (1er janvier 2026)
COG_BASE_URL = "https://www.insee.fr/fr/statistiques/fichier/8740222/"


class Settings(BaseModel):
    """Paths used by the pipeline. Everything lives under data/, outside git."""

    data_dir: Path = Path("data")

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def manifest_path(self) -> Path:
        return self.data_dir / "manifest.jsonl"

    @property
    def warehouse_path(self) -> Path:
        return self.data_dir / "warehouse.duckdb"

    @property
    def cog_dir(self) -> Path:
        return self.data_dir / "reference" / "cog"
