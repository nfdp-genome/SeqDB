from __future__ import annotations

import json
from pathlib import Path

import anyio
import typer
from rich.console import Console

from seqdb_cli.client import SeqDBClient
from seqdb_cli.config import CONFIG_PATH, load_config

console = Console()


def ingest(
    accession: str = typer.Argument(..., help="Project or sample accession"),
    multiqc: Path = typer.Option(..., "--multiqc", help="Path to multiqc_data/ directory"),
) -> None:
    """Ingest pipeline results (MultiQC) back into SeqDB."""
    cfg = load_config(CONFIG_PATH)
    client = SeqDBClient(cfg)

    async def _ingest():
        try:
            mqc_json = multiqc / "multiqc_data.json"
            if not mqc_json.exists():
                console.print(f"[red]Not found: {mqc_json}[/red]")
                raise typer.Exit(1)

            with open(mqc_json) as f:
                mqc_data = json.load(f)

            general_stats = mqc_data.get("report_general_stats_data", [])
            sample_stats: dict[str, dict] = {}
            for stats_block in general_stats:
                for sample_name, metrics in stats_block.items():
                    if sample_name not in sample_stats:
                        sample_stats[sample_name] = {}
                    sample_stats[sample_name].update(metrics)

            if not sample_stats:
                console.print("[yellow]No sample stats found in MultiQC data[/yellow]")
                raise typer.Exit(1)

            with open(mqc_json, "rb") as f:
                resp = await client.post(
                    "/api/v1/staging/upload",
                    files={"file": ("multiqc_data.json", f, "application/json")},
                )
            if resp.status_code == 200:
                console.print("[green]MultiQC data uploaded[/green]")

            console.print(f"[green]QC data ingested[/green] for {len(sample_stats)} samples")
            for name, stats in sample_stats.items():
                total_seq = stats.get("total_sequences", "N/A")
                avg_len = stats.get("avg_sequence_length", "N/A")
                console.print(f"  {name}: {total_seq:,} reads, avg length {avg_len}")
        finally:
            await client.close()

    anyio.run(_ingest)
