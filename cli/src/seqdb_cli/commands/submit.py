from __future__ import annotations

from pathlib import Path

import anyio
import typer
from rich.console import Console
from rich.table import Table

from seqdb_cli.client import SeqDBClient
from seqdb_cli.config import CONFIG_PATH, load_config
from seqdb_cli.transfer import upload_files
from seqdb_cli.utils import discover_sequence_files

console = Console()


def template(
    checklist_id: str = typer.Argument(..., help="Checklist ID (e.g. ERC000011)"),
    output: Path = typer.Option("template.tsv", "--output", "-o", help="Output file path"),
) -> None:
    """Download a sample sheet template for a checklist."""
    cfg = load_config(CONFIG_PATH)
    client = SeqDBClient(cfg)

    async def _fetch():
        try:
            resp = await client.get(f"/api/v1/bulk-submit/template/{checklist_id}")
            resp.raise_for_status()
            output.write_bytes(resp.content)
            console.print(f"[green]Template saved[/green] to {output}")
        finally:
            await client.close()

    anyio.run(_fetch)


def upload(
    files: list[Path] = typer.Argument(..., help="Files to upload to staging"),
    threads: int = typer.Option(4, "--threads", "-t", help="Concurrent uploads"),
) -> None:
    """Upload files to the SeqDB staging area."""
    cfg = load_config(CONFIG_PATH)

    async def _upload():
        results = await upload_files(
            base_url=cfg.server_url,
            token=cfg.access_token,
            files=files,
            max_concurrent=threads,
        )
        console.print(f"[green]Uploaded {len(results)} files[/green] to staging.")
        for r in results:
            console.print(f"  {r['filename']} (MD5: {r['md5'][:8]}...)")

    anyio.run(_upload)


def validate(
    sample_sheet: Path = typer.Argument(..., help="Sample sheet TSV file"),
    checklist: str = typer.Option(..., "--checklist", "-c", help="Checklist ID"),
) -> None:
    """Validate a sample sheet against a checklist."""
    cfg = load_config(CONFIG_PATH)
    client = SeqDBClient(cfg)

    async def _validate():
        try:
            with open(sample_sheet, "rb") as f:
                resp = await client.post(
                    "/api/v1/bulk-submit/validate",
                    files={"file": (sample_sheet.name, f, "text/tab-separated-values")},
                    data={"checklist_id": checklist},
                )
            resp.raise_for_status()
            report = resp.json()
            _print_validation_report(report)
        finally:
            await client.close()

    anyio.run(_validate)


def submit(
    sample_sheet: Path = typer.Argument(..., help="Sample sheet TSV file"),
    checklist: str = typer.Option(..., "--checklist", "-c", help="Checklist ID"),
    project: str = typer.Option(..., "--project", "-p", help="Project accession"),
    files_dir: Path | None = typer.Option(None, "--files", "-f", help="Directory of files to upload"),
    threads: int = typer.Option(4, "--threads", "-t", help="Concurrent transfers"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Upload files, validate, and submit in one step."""
    cfg = load_config(CONFIG_PATH)
    client = SeqDBClient(cfg)

    async def _submit():
        try:
            if files_dir:
                seq_files = discover_sequence_files(files_dir)
                if not seq_files:
                    console.print(f"[red]No sequence files found in {files_dir}[/red]")
                    raise typer.Exit(1)
                console.print(f"Found {len(seq_files)} files to upload...")
                await upload_files(
                    base_url=cfg.server_url,
                    token=cfg.access_token,
                    files=seq_files,
                    max_concurrent=threads,
                )

            console.print("Validating sample sheet...")
            with open(sample_sheet, "rb") as f:
                resp = await client.post(
                    "/api/v1/bulk-submit/validate",
                    files={"file": (sample_sheet.name, f, "text/tab-separated-values")},
                    data={"checklist_id": checklist},
                )
            resp.raise_for_status()
            report = resp.json()
            _print_validation_report(report)

            if not report.get("valid"):
                console.print("[red]Validation failed. Fix errors and retry.[/red]")
                raise typer.Exit(1)

            row_count = len(report.get("rows", []))
            if not yes:
                typer.confirm(f"Create {row_count} samples with associated experiments and runs?", abort=True)

            with open(sample_sheet, "rb") as f:
                confirm_resp = await client.post(
                    "/api/v1/bulk-submit/confirm",
                    files={"file": (sample_sheet.name, f, "text/tab-separated-values")},
                    data={"checklist_id": checklist, "project_accession": project},
                )
            confirm_resp.raise_for_status()
            result = confirm_resp.json()

            console.print(f"\n[green]Submission complete![/green]")
            console.print(f"  Samples created: {result.get('samples_created', 0)}")
            console.print(f"  Experiments created: {result.get('experiments_created', 0)}")
            console.print(f"  Runs created: {result.get('runs_created', 0)}")
        finally:
            await client.close()

    anyio.run(_submit)


def _print_validation_report(report: dict) -> None:
    if report.get("valid"):
        console.print("[green]Validation passed[/green]")
    else:
        console.print("[red]Validation failed[/red]")

    rows = report.get("rows", [])
    if rows:
        table = Table(title="Validation Report")
        table.add_column("Row", style="dim")
        table.add_column("Sample")
        table.add_column("Status")
        table.add_column("Issues")

        for row in rows:
            errors = row.get("errors", [])
            warnings = row.get("warnings", [])
            status = "[green]OK" if not errors else "[red]FAIL"
            if not errors and warnings:
                status = "[yellow]WARN"
            issues = "; ".join(errors + warnings) or "—"
            table.add_row(str(row["row_num"]), row.get("sample_alias", "—"), status, issues)

        console.print(table)

    for err in report.get("errors", []):
        console.print(f"  [red]Error:[/red] {err}")
