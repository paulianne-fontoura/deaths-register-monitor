import hashlib

import httpx

from drm import download

CONTENT = b"A" * 176 + b"\n" + b"B" * 176 + b"\n"


def test_fetch_to_temp_writes_file_and_hash(httpx_mock, tmp_path):
    httpx_mock.add_response(url="https://example.org/deces.txt", content=CONTENT)
    with httpx.Client() as client:
        temp_path, sha256, size = download.fetch_to_temp(
            client, "https://example.org/deces.txt", tmp_path / "raw"
        )
    assert temp_path.read_bytes() == CONTENT
    assert sha256 == hashlib.sha256(CONTENT).hexdigest()
    assert size == len(CONTENT)
