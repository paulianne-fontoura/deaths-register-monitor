"""Project settings and constants."""

from pathlib import Path

from pydantic import BaseModel

DATASET_API = "https://www.data.gouv.fr/api/1/datasets/fichier-des-personnes-decedees/"
RECORD_LENGTH = 176


class Settings(BaseModel):
    """Paths used by the pipeline. Everything lives under data/, outside git."""

    data_dir: Path = Path("data")

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def manifest_path(self) -> Path:
        return self.data_dir / "manifest.jsonl"
