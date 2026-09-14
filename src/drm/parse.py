"""Fixed-width parsing of the register into parquet, with quarantine.

The official record layout (dessin d'enregistrement, INSEE) defines nine
fields over positions 1-176. Real lines carry trailing non-significant
characters beyond position 176; they are ignored. Lines too short to cut
every field are quarantined with a reason, never fixed silently.
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import BaseModel, Field, ValidationError

from drm.config import RECORD_LENGTH

# (name, start position, length) - positions are 1-based, as in the INSEE layout.
FIELDS = [
    ("nom_prenoms", 1, 80),
    ("sexe", 81, 1),
    ("date_naissance", 82, 8),
    ("code_lieu_naissance", 90, 5),
    ("commune_naissance", 95, 30),
    ("pays_naissance", 125, 30),
    ("date_deces", 155, 8),
    ("code_lieu_deces", 163, 5),
    ("numero_acte", 168, 9),
]

SAMPLE_SIZE = 1000


class DeathRecord(BaseModel):
    """Shape of one parsed record; used to validate a sample of every file."""

    nom_prenoms: str
    sexe: str = Field(pattern=r"^[12]$")
    date_naissance: str = Field(pattern=r"^\d{8}$")
    code_lieu_naissance: str
    commune_naissance: str
    pays_naissance: str
    date_deces: str = Field(pattern=r"^\d{8}$")
    code_lieu_deces: str
    numero_acte: str


def decode_file(path: Path) -> tuple[str, list[str]]:
    """Read the whole file, utf-8 first, latin-1 as documented fallback."""
    raw = path.read_bytes()
    try:
        return "utf-8", raw.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return "latin-1", raw.decode("latin-1").splitlines()


def cut_line(line: str) -> dict:
    record = {}
    for name, start, length in FIELDS:
        value = line[start - 1 : start - 1 + length]
        record[name] = value.strip() if name != "sexe" else value
    return record


def parse_file(
    raw_path: Path,
    file_hash: str,
    parquet_path: Path,
    quarantine_path: Path,
) -> dict:
    """Parse one raw file into parquet; quarantine unusable lines.

    Returns stats: rows, quarantined, encoding, sample_errors.
    """
    encoding, lines = decode_file(raw_path)
    ingested_at = datetime.now(UTC).isoformat(timespec="seconds")

    records: list[dict] = []
    quarantined: list[dict] = []
    sample_errors = 0

    for line_number, line in enumerate(lines, start=1):
        if len(line) < RECORD_LENGTH:
            quarantined.append(
                {
                    "line_number": line_number,
                    "reason": "short_line",
                    "length": len(line),
                }
            )
            continue
        record = cut_line(line)
        if len(records) < SAMPLE_SIZE:
            try:
                DeathRecord(**record)
            except ValidationError:
                sample_errors += 1
        record["_line_number"] = line_number
        record["_row_hash"] = hashlib.sha256(line.encode("utf-8")).hexdigest()
        record["_source_file"] = raw_path.name
        record["_file_hash"] = file_hash
        record["_ingested_at"] = ingested_at
        records.append(record)

    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    columns = [name for name, _, _ in FIELDS] + [
        "_line_number",
        "_row_hash",
        "_source_file",
        "_file_hash",
        "_ingested_at",
    ]
    table = pa.table(
        {column: [record[column] for record in records] for column in columns}
    )
    pq.write_table(table, parquet_path)

    if quarantined:
        quarantine_path.parent.mkdir(parents=True, exist_ok=True)
        with open(quarantine_path, "w", encoding="utf-8") as handle:
            handle.writelines(json.dumps(entry) + "\n" for entry in quarantined)

    return {
        "rows": len(records),
        "quarantined": len(quarantined),
        "encoding": encoding,
        "sample_errors": sample_errors,
    }
