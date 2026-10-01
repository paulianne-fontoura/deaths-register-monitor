"""deaths-register-monitor command line interface."""

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import duckdb
import httpx
import typer

from drm import cog as cog_module
from drm import download, manifest, registry, validate, warehouse
from drm import parse as parse_module
from drm import publish as publish_module
from drm.config import RECORD_LENGTH, Settings

app = typer.Typer(no_args_is_help=True, help="deaths-register-monitor - ingestion CLI")


@app.callback()
def main() -> None:
    """Continuous quality audit of the French national death register."""


def _download_resource(
    client: httpx.Client, settings: Settings, resource: dict, period: str
) -> tuple[Path, str, str, dict | None]:
    """Fetch one resource into the raw layer (ADR-003).

    Returns (raw_path, sha256, status, stats). Status 'unchanged' means this
    exact content is already in the manifest and raw_path points at it;
    'new' means a new version was written and recorded.
    """
    entries = manifest.load(settings.manifest_path)
    temp_path, sha256, size = download.fetch_to_temp(
        client, resource["url"], settings.raw_dir
    )
    if manifest.seen(entries, resource["title"], sha256):
        existing = next(
            entry
            for entry in entries
            if entry.get("title") == resource["title"] and entry.get("sha256") == sha256
        )
        local = manifest.local_path(existing)
        if local.exists():
            temp_path.unlink()
        else:
            # content already captured, file absent here (fresh clone of the
            # versioned manifest) - keep the download where the manifest says
            local.parent.mkdir(parents=True, exist_ok=True)
            temp_path.replace(local)
        return local, sha256, "unchanged", None
    final_path = manifest.next_version_path(settings.raw_dir, resource["title"])
    temp_path.replace(final_path)
    stats = validate.check_fixed_width(final_path)
    manifest.append(
        settings.manifest_path,
        {
            "period": period,
            "title": resource["title"],
            "url": resource["url"],
            "path": str(final_path),
            "sha256": sha256,
            "bytes": size,
            "lines": stats["lines"],
            "bad_lines": stats["bad_lines"],
            "downloaded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        },
    )
    return final_path, sha256, "new", {"bytes": size, **stats}


def _parse_raw(settings: Settings, raw_path: Path, file_hash: str) -> tuple[Path, dict]:
    """Parse one raw file into the parquet layer, quarantining bad lines."""
    parquet_path = settings.data_dir / "parquet" / f"{raw_path.name}.parquet"
    quarantine_path = settings.data_dir / "quarantine" / f"{raw_path.name}.jsonl"
    stats = parse_module.parse_file(raw_path, file_hash, parquet_path, quarantine_path)
    return parquet_path, stats


@app.command()
def ingest(
    source: str = typer.Argument(help="Data source. Only 'deaths' is supported."),
    month: str = typer.Option(
        ..., "--month", help="Period: '2026-08' (monthly) or '2025' (annual)."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Resolve and show the plan, download nothing."
    ),
    parse_after: bool = typer.Option(
        False, "--parse", help="Parse the downloaded file into parquet right away."
    ),
    load_after: bool = typer.Option(
        False, "--load", help="Load the parquet into the warehouse. Requires --parse."
    ),
) -> None:
    """Download one delivery of the death register into the raw layer."""
    if source != "deaths":
        raise typer.BadParameter("only 'deaths' is supported")
    if load_after and not parse_after:
        raise typer.BadParameter("--load requires --parse")
    settings = Settings()
    with httpx.Client() as client:
        resource = registry.resolve(client, month)
        typer.echo(f"resource: {resource['title']}")
        typer.echo(f"url:      {resource['url']}")
        if dry_run:
            typer.echo("dry-run:  nothing downloaded")
            return

        raw_path, sha256, status, stats = _download_resource(
            client, settings, resource, month
        )
        if status == "unchanged":
            typer.echo(
                f"unchanged: sha256 {sha256[:12]}... already in the manifest, nothing to do"
            )
            return
        typer.echo(f"saved:    {raw_path} ({stats['bytes']} bytes)")
        typer.echo(f"sha256:   {sha256}")
        typer.echo(
            f"lines:    {stats['lines']} ({stats['bad_lines']} shorter than {RECORD_LENGTH} chars)"
        )
        if parse_after:
            parquet_path, parse_stats = _parse_raw(settings, raw_path, sha256)
            typer.echo(f"parquet:  {parquet_path} ({parse_stats['rows']} rows)")
            if load_after:
                con = warehouse.connect(settings.warehouse_path)
                load_stats = warehouse.load_raw(con, parquet_path, sha256)
                typer.echo(f"loaded:   {load_stats['inserted']} new rows in raw_deces")


@app.command()
def backfill(
    source: str = typer.Argument(help="Data source. Only 'deaths' is supported."),
    from_year: int = typer.Option(1970, "--from", help="First year to load."),
    to_year: int = typer.Option(2026, "--to", help="Last year to load."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show the plan, download and load nothing."
    ),
    all_deliveries: bool = typer.Option(
        False,
        "--all-deliveries",
        help="Version corpus (ADR-008): every delivery, monthly overlaps included.",
    ),
) -> None:
    """Load the register history into the warehouse, one file at a time.

    By default annual files take precedence over monthly increments
    (ADR-004, base corpus). With --all-deliveries the monthly increments of
    covered years are loaded too (ADR-008, version corpus): the overlaps
    feed fct_record_versions. A file already in the manifest is not
    downloaded again and a file already in the warehouse is not loaded
    again, so an interrupted run just resumes.
    """
    if source != "deaths":
        raise typer.BadParameter("only 'deaths' is supported")
    if from_year > to_year:
        raise typer.BadParameter("--from must not be after --to")
    settings = Settings()
    started = time.perf_counter()
    with httpx.Client() as client:
        dataset = registry.fetch_dataset(client)
        plan = (
            registry.version_resources(dataset, from_year, to_year)
            if all_deliveries
            else registry.backfill_resources(dataset, from_year, to_year)
        )
        typer.echo(f"plan: {len(plan)} files ({from_year}-{to_year})")
        if dry_run:
            entries = manifest.load(settings.manifest_path)
            for resource in plan:
                known = manifest.latest(entries, resource["title"])
                present = known and manifest.local_path(known).exists()
                state = "in manifest" if present else "to download"
                typer.echo(f"  {resource['title']}  [{state}]")
            typer.echo("dry-run: nothing downloaded")
            return

        con = warehouse.connect(settings.warehouse_path)
        failures: list[str] = []
        for index, resource in enumerate(plan, start=1):
            prefix = f"[{index}/{len(plan)}] {resource['title']}"
            try:
                entries = manifest.load(settings.manifest_path)
                known = manifest.latest(entries, resource["title"])
                if known and manifest.local_path(known).exists():
                    raw_path, sha256 = manifest.local_path(known), known["sha256"]
                    origin = "manifest"
                else:
                    period = registry.title_to_period(resource["title"])
                    raw_path, sha256, _, _ = _download_resource(
                        client, settings, resource, period
                    )
                    origin = "downloaded"
                if warehouse.is_loaded(con, sha256):
                    typer.echo(f"{prefix}: already loaded")
                    continue
                parquet_path = (
                    settings.data_dir / "parquet" / f"{raw_path.name}.parquet"
                )
                if not parquet_path.exists():
                    parquet_path, _ = _parse_raw(settings, raw_path, sha256)
                load_stats = warehouse.load_raw(con, parquet_path, sha256)
                typer.echo(
                    f"{prefix}: {origin}, "
                    f"{load_stats['inserted']} rows in {load_stats['seconds']}s"
                )
            except Exception as error:  # noqa: BLE001 - one file must not stop the run
                failures.append(resource["title"])
                typer.echo(f"{prefix}: FAILED ({error})")
        typer.echo(f"warehouse: {warehouse.count_rows(con)} rows")
        typer.echo(f"elapsed:   {round(time.perf_counter() - started)}s")
        if failures:
            typer.echo(f"failed:    {', '.join(failures)}")
            raise typer.Exit(code=1)


@app.command()
def cog(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="List the files, download nothing."
    ),
) -> None:
    """Download the geographic referentials (COG) into the reference layer."""
    settings = Settings()
    if dry_run:
        for name in cog_module.COG_FILES:
            typer.echo(f"  {name}")
        typer.echo("dry-run: nothing downloaded")
        return
    with httpx.Client() as client:
        results = cog_module.download_cog(client, settings)
    for name, status in results:
        typer.echo(f"{name}: {status}")
    typer.echo(f"reference: {settings.cog_dir}")


@app.command()
def probe(
    json_path: Annotated[
        Path | None,
        typer.Option("--json", help="Write the full report to this file as JSON."),
    ] = None,
) -> None:
    """Compare data.gouv deliveries with the local capture manifest (ADR-009).

    Read-only and side-effect free - downloads nothing, exits 0 whatever the
    findings. The monitoring workflows parse the JSON report and open or
    close the capture issue from it; a non-zero exit is reserved for real
    errors (API unreachable, malformed manifest).
    """
    settings = Settings()
    with httpx.Client() as client:
        dataset = registry.fetch_dataset(client)
    entries = manifest.load(settings.manifest_path)
    report = registry.probe_report(dataset, entries)
    report["checked_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    typer.echo(f"listed:   {report['resources_listed']} deliveries on data.gouv")
    typer.echo(f"captured: {report['captured_current']} already in the manifest")
    typer.echo(f"new:      {len(report['new_deliveries'])} to capture")
    for resource in report["new_deliveries"]:
        typer.echo(f"  {resource['title']} (published {resource['published_at']})")
    typer.echo(
        f"retired:  {len(report['vanished_captured'])} no longer listed, all captured"
    )
    if report["new_deliveries"]:
        typer.echo("hint:     uv run drm backfill deaths --all-deliveries")
    if json_path is not None:
        json_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        typer.echo(f"report:   {json_path}")


@app.command()
def publish(
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Export and check the marts, load nothing."),
    ] = False,
) -> None:
    """Publish the aggregate marts to the BigQuery sandbox (ADR-010).

    Exports the allowlisted aggregate marts to parquet, refusing any
    nominative column, then loads them into the drm_exports dataset. The
    load needs the bq dependency group and the DBT_BQ_PROJECT and
    DRM_BQ_KEYFILE environment variables; --dry-run needs neither.
    """
    settings = Settings()
    con = duckdb.connect(str(settings.warehouse_path), read_only=True)
    files = publish_module.export_marts(
        con, settings.data_dir / "exports", publish_module.PUBLISHABLE_MARTS
    )
    con.close()
    for mart, path, rows in files:
        typer.echo(f"exported: {mart} ({rows} rows) -> {path}")
    if dry_run:
        typer.echo("dry-run:  nothing loaded")
        return
    project = os.environ.get("DBT_BQ_PROJECT")
    keyfile = os.environ.get("DRM_BQ_KEYFILE")
    if not project or not keyfile:
        raise typer.BadParameter("set DBT_BQ_PROJECT and DRM_BQ_KEYFILE first")
    # imported here, not at module level - the bq dependency group is optional
    from google.cloud import bigquery
    from google.oauth2 import service_account

    credentials = service_account.Credentials.from_service_account_file(keyfile)
    client = bigquery.Client(
        project=project, credentials=credentials, location=publish_module.LOCATION
    )
    for table_id, rows in publish_module.load_to_bigquery(client, bigquery, files):
        typer.echo(f"loaded:   {table_id} ({rows} rows)")


@app.command()
def parse(
    raw_file: Annotated[
        Path,
        typer.Argument(help="A file from data/raw to parse into parquet.", exists=True),
    ],
) -> None:
    """Parse one raw delivery into the parquet layer, quarantining bad lines."""
    settings = Settings()
    entries = manifest.load(settings.manifest_path)
    file_hash = next(
        (
            e["sha256"]
            for e in entries
            if e.get("path") and manifest.local_path(e) == raw_file
        ),
        "unknown",
    )
    parquet_path, stats = _parse_raw(settings, raw_file, file_hash)
    typer.echo(f"rows:        {stats['rows']}")
    typer.echo(f"quarantined: {stats['quarantined']}")
    typer.echo(f"encoding:    {stats['encoding']}")
    typer.echo(
        f"sample:      {stats['sample_errors']} validation errors in the first 1000 rows"
    )
    typer.echo(f"parquet:     {parquet_path}")
    if stats["quarantined"]:
        quarantine_path = settings.data_dir / "quarantine" / f"{raw_file.name}.jsonl"
        typer.echo(f"quarantine:  {quarantine_path}")
