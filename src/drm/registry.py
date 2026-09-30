"""Resolve a period to its file resource on data.gouv.fr.

The INSEE dataset lists one resource per file (deces-2026-m08.txt, deces-2025.txt...).
Resource ids change when files are republished, so we resolve by title at run time
instead of hardcoding urls.
"""

import re

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from drm.config import DATASET_API

ANNUAL_RE = re.compile(r"^deces-(\d{4})\.txt$")
MONTHLY_RE = re.compile(r"^deces-(\d{4})-m(\d{2})\.txt$")
PUBLISHED_RE = re.compile(r"/(\d{8})-\d{6}/")


class ResourceNotFoundError(Exception):
    """The requested period has no matching file in the dataset."""


def period_to_title(period: str) -> str:
    """Map '2026-08' to 'deces-2026-m08.txt' and '2025' to 'deces-2025.txt'."""
    if "-" in period:
        year, month = period.split("-", 1)
        return f"deces-{year}-m{int(month):02d}.txt"
    return f"deces-{period}.txt"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, max=10),
    reraise=True,
)
def fetch_dataset(client: httpx.Client) -> dict:
    response = client.get(DATASET_API, timeout=30)
    response.raise_for_status()
    return response.json()


def title_to_period(title: str) -> str:
    """Inverse of period_to_title, for manifest entries written by backfill."""
    if match := MONTHLY_RE.match(title):
        return f"{match.group(1)}-{match.group(2)}"
    if match := ANNUAL_RE.match(title):
        return match.group(1)
    return title


def _classify_resources(
    dataset: dict,
) -> tuple[dict[int, dict], dict[int, list[dict]]]:
    """Split the dataset resources into annual and monthly files by year."""
    annual: dict[int, dict] = {}
    monthly: dict[int, list[dict]] = {}
    for resource in dataset.get("resources", []):
        title = resource.get("title", "")
        if match := ANNUAL_RE.match(title):
            annual[int(match.group(1))] = {"title": title, "url": resource["url"]}
        elif match := MONTHLY_RE.match(title):
            monthly.setdefault(int(match.group(1)), []).append(
                {"title": title, "url": resource["url"]}
            )
    return annual, monthly


def backfill_resources(dataset: dict, from_year: int, to_year: int) -> list[dict]:
    """Ordered download plan for the base corpus (ADR-004).

    A year covered by an annual file uses it alone; a year without one (the
    current year) falls back to its monthly increments. Quarterly files and
    unrelated resources never match the patterns, so they are excluded.
    """
    annual, monthly = _classify_resources(dataset)
    plan: list[dict] = []
    for year in range(from_year, to_year + 1):
        if year in annual:
            plan.append(annual[year])
        else:
            plan.extend(sorted(monthly.get(year, []), key=lambda r: r["title"]))
    return plan


def version_resources(dataset: dict, from_year: int, to_year: int) -> list[dict]:
    """Ordered download plan for the version corpus (ADR-008).

    Every delivery in range, annual and monthly alike: the overlaps between
    an annual file and the monthly increments of the same year are the
    signal fct_record_versions reads corrections and late arrivals from.
    Quarterly files stay excluded (ADR-004).
    """
    annual, monthly = _classify_resources(dataset)
    plan: list[dict] = []
    for year in range(from_year, to_year + 1):
        if year in annual:
            plan.append(annual[year])
        plan.extend(sorted(monthly.get(year, []), key=lambda r: r["title"]))
    return plan


def _published_date(url: str) -> str | None:
    """Upload date embedded in a versioned data.gouv url, as 'YYYY-MM-DD'."""
    if match := PUBLISHED_RE.search(url):
        raw = match.group(1)
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
    return None


def probe_report(dataset: dict, entries: list[dict]) -> dict:
    """Compare the deliveries data.gouv lists with the capture manifest.

    The manifest is append-only and keeps one entry per captured version, so
    a listed url the manifest does not know is a delivery to capture - a new
    monthly increment, or a republication of an existing title under a new
    versioned url. A captured title data.gouv no longer lists was retired
    (monthly increments are deleted at annual consolidation, ADR-008); it is
    reported for the audit trail, never as a failure. A file published then
    retired between two probes would be invisible here - that risk is what
    the weekly cadence bounds (ADR-009).
    """
    annual, monthly = _classify_resources(dataset)
    listed: list[dict] = list(annual.values())
    for year_resources in monthly.values():
        listed.extend(year_resources)
    register_entries = [
        entry
        for entry in entries
        if ANNUAL_RE.match(entry.get("title", ""))
        or MONTHLY_RE.match(entry.get("title", ""))
    ]
    captured_urls = {entry.get("url") for entry in register_entries}
    new_deliveries = sorted(
        (
            {**resource, "published_at": _published_date(resource["url"])}
            for resource in listed
            if resource["url"] not in captured_urls
        ),
        key=lambda resource: resource["title"],
    )
    listed_titles = {resource["title"] for resource in listed}
    vanished_captured = sorted(
        {entry["title"] for entry in register_entries} - listed_titles
    )
    return {
        "resources_listed": len(listed),
        "captured_current": len(listed) - len(new_deliveries),
        "new_deliveries": new_deliveries,
        "vanished_captured": vanished_captured,
    }


def resolve(client: httpx.Client, period: str) -> dict:
    """Return {'title', 'url'} for the file covering the given period."""
    title = period_to_title(period)
    dataset = fetch_dataset(client)
    for resource in dataset.get("resources", []):
        if resource.get("title") == title:
            return {"title": title, "url": resource["url"]}
    raise ResourceNotFoundError(f"no resource named {title} in the dataset")
