"""deaths-register-monitor command line interface."""

from datetime import UTC, datetime

import httpx
import typer

from drm import download, manifest, registry, validate
from drm.config import RECORD_LENGTH, Settings

app = typer.Typer(no_args_is_help=True, help="deaths-register-monitor - ingestion CLI")


@app.callback()
def main() -> None:
    """Continuous quality audit of the French national death register."""


@app.command()
def ingest(
    source: str = typer.Argument(help="Data source. Only 'deaths' is supported."),
    month: str = typer.Option(
        ..., "--month", help="Period: '2026-08' (monthly) or '2025' (annual)."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Resolve and show the plan, download nothing."
    ),
) -> None:
    """Download one delivery of the death register into the raw layer."""
    if source != "deaths":
        raise typer.BadParameter("only 'deaths' is supported")
    settings = Settings()
    with httpx.Client() as client:
        resource = registry.resolve(client, month)
        typer.echo(f"resource: {resource['title']}")
        typer.echo(f"url:      {resource['url']}")
        if dry_run:
            typer.echo("dry-run:  nothing downloaded")
            return

        entries = manifest.load(settings.manifest_path)
        temp_path, sha256, size = download.fetch_to_temp(
            client, resource["url"], settings.raw_dir
        )
        if manifest.seen(entries, resource["title"], sha256):
            temp_path.unlink()
            typer.echo(
                f"unchanged: sha256 {sha256[:12]}... already in the manifest, nothing to do"
            )
            return

        final_path = manifest.next_version_path(settings.raw_dir, resource["title"])
        temp_path.replace(final_path)
        stats = validate.check_fixed_width(final_path)
        manifest.append(
            settings.manifest_path,
            {
                "period": month,
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
        typer.echo(f"saved:    {final_path} ({size} bytes)")
        typer.echo(f"sha256:   {sha256}")
        typer.echo(
            f"lines:    {stats['lines']} ({stats['bad_lines']} shorter than {RECORD_LENGTH} chars)"
        )
