import httpx
import pytest

from drm import registry
from drm.config import DATASET_API


def test_period_to_title_monthly():
    assert registry.period_to_title("2026-08") == "deces-2026-m08.txt"


def test_period_to_title_annual():
    assert registry.period_to_title("2025") == "deces-2025.txt"


def test_resolve_finds_resource(httpx_mock):
    httpx_mock.add_response(
        url=DATASET_API,
        json={
            "resources": [
                {"title": "deces-2026-m08.txt", "url": "https://example.org/m08.txt"},
                {"title": "deces-2025.txt", "url": "https://example.org/2025.txt"},
            ]
        },
    )
    with httpx.Client() as client:
        resource = registry.resolve(client, "2026-08")
    assert resource == {
        "title": "deces-2026-m08.txt",
        "url": "https://example.org/m08.txt",
    }


def test_resolve_unknown_period_raises(httpx_mock):
    httpx_mock.add_response(url=DATASET_API, json={"resources": []})
    with httpx.Client() as client, pytest.raises(registry.ResourceNotFoundError):
        registry.resolve(client, "1969")
