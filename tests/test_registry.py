import httpx
import pytest

from drm import registry
from drm.config import DATASET_API


def test_period_to_title_monthly():
    assert registry.period_to_title("2026-08") == "deces-2026-m08.txt"


def test_period_to_title_annual():
    assert registry.period_to_title("2025") == "deces-2025.txt"


def test_title_to_period_round_trip():
    assert registry.title_to_period("deces-2026-m08.txt") == "2026-08"
    assert registry.title_to_period("deces-1970.txt") == "1970"


def test_backfill_resources_prefers_annual_and_skips_quarterly():
    dataset = {
        "resources": [
            {"title": "deces-2025.txt", "url": "u-2025"},
            {"title": "deces-2025-m03.txt", "url": "u-2025-m03"},
            {"title": "deces-2026-m02.txt", "url": "u-m02"},
            {"title": "deces-2026-m01.txt", "url": "u-m01"},
            {"title": "deces-2026-t1.txt", "url": "u-t1"},
        ]
    }
    plan = registry.backfill_resources(dataset, 2025, 2026)
    assert [r["title"] for r in plan] == [
        "deces-2025.txt",  # annual wins over 2025 monthlies (ADR-004)
        "deces-2026-m01.txt",  # no annual for 2026: monthlies, sorted
        "deces-2026-m02.txt",
    ]


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
