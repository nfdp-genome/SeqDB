from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import anyio
import typer
from rich.console import Console

from seqdb_cli.client import SeqDBClient
from seqdb_cli.config import CONFIG_PATH, load_config
from seqdb_cli.formats import get_formatter
from seqdb_cli.transfer import download_files

console = Console()


def fetch(
    accession: str = typer.Argument(..., help="Project, sample, or run accession"),
    output: Path = typer.Option("./seqdb-data", "--output", "-o", help="Output directory"),
    format: str = typer.Option("generic", "--format", "-f", help="Samplesheet format"),
    urls_only: bool = typer.Option(False, "--urls-only", help="Output presigned URLs instead of downloading"),
    threads: int = typer.Option(4, "--threads", "-t", help="Concurrent downloads"),
    strandedness: str = typer.Option("auto", "--strandedness", help="Strandedness for rnaseq format"),
) -> None:
    """Fetch reads and generate an nf-core-compatible samplesheet."""
    cfg = load_config(CONFIG_PATH)
    client = SeqDBClient(cfg)
    formatter = get_formatter(format)

    async def _fetch():
        try:
            samples, runs_by_sample = await _resolve_accession(client, accession)

            download_map: dict[str, list[dict[str, Any]]] = {}
            for sample_acc, runs in runs_by_sample.items():
                mapped_runs = []
                for i, run in enumerate(runs):
                    resp = await client.get(f"/api/v1/runs/{run['accession']}/download")
                    if resp.status_code == 200:
                        data = resp.json()
                        url = data.get("url", "")
                    elif resp.status_code == 307:
                        url = resp.headers.get("location", "")
                    else:
                        url = ""

                    filename = Path(run.get("file_path", "")).name
                    direction = "forward" if i % 2 == 0 else "reverse"
                    mapped_runs.append({
                        "file_path": url if urls_only else str(output / "reads" / filename),
                        "direction": direction,
                        "url": url,
                        "filename": filename,
                    })
                download_map[sample_acc] = mapped_runs

            if not urls_only:
                all_downloads = []
                for runs in download_map.values():
                    for r in runs:
                        if r["url"]:
                            all_downloads.append((r["url"], r["filename"]))
                if all_downloads:
                    reads_dir = output / "reads"
                    console.print(f"Downloading {len(all_downloads)} files...")
                    await download_files(
                        urls=all_downloads,
                        output_dir=reads_dir,
                        max_concurrent=threads,
                    )

            kwargs = {}
            if format == "rnaseq":
                kwargs["strandedness"] = strandedness
            rows = formatter.map_rows(samples, download_map, **kwargs)

            output.mkdir(parents=True, exist_ok=True)
            samplesheet_path = output / "samplesheet.csv"
            with open(samplesheet_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=formatter.columns)
                writer.writeheader()
                writer.writerows(rows)

            console.print(f"\n[green]Samplesheet written[/green] to {samplesheet_path}")
            console.print(f"  Samples: {len(samples)}")
            console.print(f"  Format: {format}")
            if not urls_only:
                console.print(f"\n  Ready: nextflow run nf-core/<pipeline> --input {samplesheet_path}")
            else:
                console.print("\n  [dim]Samplesheet contains presigned URLs (valid ~24h)[/dim]")
        finally:
            await client.close()

    anyio.run(_fetch)


async def _resolve_accession(
    client: SeqDBClient, accession: str
) -> tuple[list[dict], dict[str, list[dict]]]:
    """Resolve an accession to samples and their runs."""
    runs_by_sample: dict[str, list[dict]] = {}
    samples: list[dict] = []

    if accession.startswith("NFDP-PRJ-"):
        resp = await client.get(f"/api/v1/projects/{accession}")
        resp.raise_for_status()

        samples_resp = await client.get("/api/v1/samples/", params={"project": accession})
        samples_resp.raise_for_status()
        samples = samples_resp.json()

        for s in samples:
            runs_resp = await client.get("/api/v1/runs/", params={"sample": s["accession"]})
            if runs_resp.status_code == 200:
                runs_by_sample[s["accession"]] = runs_resp.json()

    elif accession.startswith("NFDP-SAM-"):
        resp = await client.get(f"/api/v1/samples/{accession}")
        resp.raise_for_status()
        samples = [resp.json()]

        runs_resp = await client.get("/api/v1/runs/", params={"sample": accession})
        if runs_resp.status_code == 200:
            runs_by_sample[accession] = runs_resp.json()

    elif accession.startswith("NFDP-RUN-"):
        resp = await client.get(f"/api/v1/runs/{accession}")
        resp.raise_for_status()
        run = resp.json()
        sample_acc = run.get("sample_accession", accession)
        samples = [{"accession": sample_acc, "organism": "", "external_id": None}]
        runs_by_sample[sample_acc] = [run]

    else:
        raise typer.BadParameter(f"Unrecognized accession format: {accession}")

    return samples, runs_by_sample
