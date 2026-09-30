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


def test_version_resources_keeps_monthly_overlaps():
    dataset = {
        "resources": [
            {"title": "deces-2025.txt", "url": "u-2025"},
            {"title": "deces-2025-m03.txt", "url": "u-2025-m03"},
            {"title": "deces-2026-m01.txt", "url": "u-m01"},
            {"title": "deces-2026-t1.txt", "url": "u-t1"},
        ]
    }
    plan = registry.version_resources(dataset, 2025, 2026)
    assert [r["title"] for r in plan] == [
        "deces-2025.txt",  # annual AND its monthly overlap (ADR-008)
        "deces-2025-m03.txt",
        "deces-2026-m01.txt",  # quarterly still excluded
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


VERSIONED = "https://static.data.gouv.fr/resources/fichier-des-personnes-decedees"


def test_probe_report_flags_unknown_urls_as_new():
    dataset = {
        "resources": [
            {"title": "deces-2025.txt", "url": f"{VERSIONED}/20260410-101010/d25.txt"},
            {
                "title": "deces-2026-m09.txt",
                "url": f"{VERSIONED}/20261010-090000/m09.txt",
            },
            {
                "title": "deces-2026-t3.txt",
                "url": f"{VERSIONED}/20261010-090100/t3.txt",
            },
        ]
    }
    entries = [
        {"title": "deces-2025.txt", "url": f"{VERSIONED}/20260410-101010/d25.txt"},
    ]
    report = registry.probe_report(dataset, entries)
    assert report["resources_listed"] == 2  # quarterly excluded (ADR-004)
    assert report["captured_current"] == 1
    assert [r["title"] for r in report["new_deliveries"]] == ["deces-2026-m09.txt"]
    assert report["new_deliveries"][0]["published_at"] == "2026-10-10"
    assert report["vanished_captured"] == []


def test_probe_report_republished_annual_counts_as_new():
    dataset = {
        "resources": [
            {"title": "deces-2025.txt", "url": f"{VERSIONED}/20261120-080000/d25.txt"},
        ]
    }
    entries = [
        {"title": "deces-2025.txt", "url": f"{VERSIONED}/20260410-101010/d25.txt"},
    ]
    report = registry.probe_report(dataset, entries)
    assert [r["title"] for r in report["new_deliveries"]] == ["deces-2025.txt"]
    assert report["vanished_captured"] == []  # title still listed, only the url moved


def test_probe_report_reports_retired_monthly_as_captured():
    dataset = {
        "resources": [
            {"title": "deces-2024.txt", "url": f"{VERSIONED}/20251215-080000/d24.txt"},
        ]
    }
    entries = [
        {"title": "deces-2024.txt", "url": f"{VERSIONED}/20251215-080000/d24.txt"},
        {"title": "deces-2024-m10.txt", "url": f"{VERSIONED}/20241105-080000/m10.txt"},
    ]
    report = registry.probe_report(dataset, entries)
    assert report["new_deliveries"] == []
    assert report["vanished_captured"] == ["deces-2024-m10.txt"]


def test_probe_report_ignores_cog_manifest_entries():
    dataset = {"resources": []}
    entries = [
        {"title": "v_commune_2026.csv", "url": "https://insee.fr/cog.csv"},
    ]
    report = registry.probe_report(dataset, entries)
    assert report["new_deliveries"] == []
    assert report["vanished_captured"] == []
