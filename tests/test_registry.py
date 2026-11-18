from datetime import date

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


def test_probe_report_capture_clock_survives_an_in_place_replacement():
    """Incident of 2026-11-04 - the September monthly, first published on
    5 October, was replaced in place on 16 October before any capture. The
    clock starts at the first publication, not at the replacement."""
    dataset = {
        "resources": [
            {
                "title": "deces-2026-m09.txt",
                "url": f"{VERSIONED}/20261016-061337/deces-2026-m09.txt",
                "created_at": "2026-10-05T12:21:12.299000+00:00",
            }
        ]
    }
    report = registry.probe_report(dataset, [], today=date(2026, 11, 4))
    pending = report["new_deliveries"][0]
    assert pending["published_at"] == "2026-10-16"
    assert pending["first_published_at"] == "2026-10-05"
    assert pending["pending_since"] == "2026-10-05"
    assert pending["replaced_before_capture"] is True
    assert report["sla_capture_days"] == 7
    assert report["sla_breaches"] == ["deces-2026-m09.txt"]


def test_probe_report_sla_breaks_at_seven_days():
    dataset = {
        "resources": [
            {
                "title": "deces-2026-m10.txt",
                "url": f"{VERSIONED}/20261105-080000/deces-2026-m10.txt",
                "created_at": "2026-11-05T08:00:02+00:00",
            }
        ]
    }
    on_day_six = registry.probe_report(dataset, [], today=date(2026, 11, 11))
    on_day_seven = registry.probe_report(dataset, [], today=date(2026, 11, 12))
    assert on_day_six["sla_breaches"] == []
    assert on_day_seven["sla_breaches"] == ["deces-2026-m10.txt"]
    assert on_day_seven["new_deliveries"][0]["replaced_before_capture"] is False


def test_probe_report_republication_of_a_captured_title_starts_a_new_clock():
    """An annual file captured in April and reissued in November is a new
    version to capture - its clock starts in November, not at the creation
    of the resource months earlier."""
    dataset = {
        "resources": [
            {
                "title": "deces-2025.txt",
                "url": f"{VERSIONED}/20261120-080000/d25.txt",
                "created_at": "2026-04-10T10:10:12+00:00",
            }
        ]
    }
    entries = [
        {"title": "deces-2025.txt", "url": f"{VERSIONED}/20260410-101010/d25.txt"},
    ]
    report = registry.probe_report(dataset, entries, today=date(2026, 11, 23))
    pending = report["new_deliveries"][0]
    assert pending["pending_since"] == "2026-11-20"
    assert pending["replaced_before_capture"] is False
    assert report["sla_breaches"] == []
