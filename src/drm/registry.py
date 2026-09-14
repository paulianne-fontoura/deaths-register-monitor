"""Resolve a period to its file resource on data.gouv.fr.

The INSEE dataset lists one resource per file (deces-2026-m08.txt, deces-2025.txt...).
Resource ids change when files are republished, so we resolve by title at run time
instead of hardcoding urls.
"""

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from drm.config import DATASET_API


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


def resolve(client: httpx.Client, period: str) -> dict:
    """Return {'title', 'url'} for the file covering the given period."""
    title = period_to_title(period)
    dataset = fetch_dataset(client)
    for resource in dataset.get("resources", []):
        if resource.get("title") == title:
            return {"title": title, "url": resource["url"]}
    raise ResourceNotFoundError(f"no resource named {title} in the dataset")
