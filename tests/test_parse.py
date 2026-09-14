"""Parsing tests with example files: normal, truncated line, broken encoding,
partial date - the real defects of this register."""

import pyarrow.parquet as pq

from drm.parse import parse_file


def build_line(
    nom="MARTIN*JEAN/",
    sexe="1",
    naissance="19381215",
    code_naissance="75056",
    commune="PARIS",
    pays="",
    deces="20260812",
    code_deces="75056",
    acte="181",
    trailing="",
):
    line = (
        nom.ljust(80)[:80]
        + sexe
        + naissance
        + code_naissance
        + commune.ljust(30)[:30]
        + pays.ljust(30)[:30]
        + deces
        + code_deces
        + acte.ljust(9)[:9]
    )
    assert len(line) == 176
    return line + trailing


def run(tmp_path, content: bytes):
    raw = tmp_path / "sample.txt"
    raw.write_bytes(content)
    parquet = tmp_path / "out.parquet"
    quarantine = tmp_path / "quarantine.jsonl"
    stats = parse_file(raw, "testhash", parquet, quarantine)
    return stats, parquet, quarantine


def test_normal_file(tmp_path):
    content = (
        build_line()
        + "\n"
        + build_line(nom="DUPONT*MARIE/", sexe="2", trailing="X" * 22)
        + "\n"
    ).encode("utf-8")
    stats, parquet, _ = run(tmp_path, content)
    assert stats == {
        "rows": 2,
        "quarantined": 0,
        "encoding": "utf-8",
        "sample_errors": 0,
    }
    table = pq.read_table(parquet)
    assert table.num_rows == 2
    assert table.column("nom_prenoms")[0].as_py() == "MARTIN*JEAN/"
    assert table.column("date_deces")[0].as_py() == "20260812"
    assert table.column("_source_file")[0].as_py() == "sample.txt"
    assert table.column("_file_hash")[0].as_py() == "testhash"
    assert len(table.column("_row_hash")[0].as_py()) == 64


def test_truncated_line_is_quarantined(tmp_path):
    content = (build_line() + "\n" + "LIGNE TRONQUEE" + "\n").encode("utf-8")
    stats, parquet, quarantine = run(tmp_path, content)
    assert stats["rows"] == 1
    assert stats["quarantined"] == 1
    assert '"reason": "short_line"' in quarantine.read_text()
    assert pq.read_table(parquet).num_rows == 1


def test_broken_encoding_falls_back_to_latin1(tmp_path):
    line = build_line(nom="NOE*RENE/", commune="NIMES")
    content = line.encode("latin-1").replace(
        b"NIMES", b"N\xcemes"
    )  # invalid utf-8 byte
    stats, parquet, _ = run(tmp_path, content + b"\n")
    assert stats["encoding"] == "latin-1"
    assert stats["rows"] == 1
    assert pq.read_table(parquet).column("commune_naissance")[0].as_py() == "NÎmes"


def test_partial_date_is_kept(tmp_path):
    content = (build_line(naissance="19450700") + "\n").encode("utf-8")
    stats, parquet, _ = run(tmp_path, content)
    assert stats == {
        "rows": 1,
        "quarantined": 0,
        "encoding": "utf-8",
        "sample_errors": 0,
    }
    assert pq.read_table(parquet).column("date_naissance")[0].as_py() == "19450700"


def test_invalid_sexe_counts_as_sample_error(tmp_path):
    content = (build_line(sexe="3") + "\n").encode("utf-8")
    stats, _, _ = run(tmp_path, content)
    assert stats["rows"] == 1
    assert stats["sample_errors"] == 1
