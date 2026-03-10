# cli/src/seqdb_cli/commands/status.py
from __future__ import annotations

import anyio
import typer
from rich.console import Console
from rich.table import Table

from seqdb_cli.client import SeqDBClient
from seqdb_cli.config import CONFIG_PATH, load_config

console = Console()


def status(
    accession: str = typer.Argument(None, help="Accession to check (project, sample, run, submission)"),
) -> None:
    """Check the status of a submission or list recent projects."""
    cfg = load_config(CONFIG_PATH)
    client = SeqDBClient(cfg)

    async def _status():
        try:
            if accession is None:
                resp = await client.get("/api/v1/projects/")
                resp.raise_for_status()
                projects = resp.json()
                table = Table(title="Recent Projects")
                table.add_column("Accession")
                table.add_column("Title")
                table.add_column("Type")
                for p in projects[:20]:
                    table.add_row(p["accession"], p["title"], p.get("project_type", ""))
                console.print(table)
            elif accession.startswith("NFDP-PRJ-"):
                resp = await client.get(f"/api/v1/projects/{accession}")
                resp.raise_for_status()
                p = resp.json()
                console.print(f"[bold]{p['accession']}[/bold] — {p['title']}")
                console.print(f"  Type: {p.get('project_type', 'N/A')}")
                console.print(f"  Created: {p.get('created_at', 'N/A')}")
            elif accession.startswith("NFDP-SUB-"):
                resp = await client.get(f"/api/v1/submissions/{accession}")
                resp.raise_for_status()
                s = resp.json()
                console.print(f"[bold]{s.get('submission_id', accession)}[/bold] — {s['title']}")
                console.print(f"  Status: {s['status']}")
            else:
                for endpoint in ["projects", "samples", "runs"]:
                    resp = await client.get(f"/api/v1/{endpoint}/{accession}")
                    if resp.status_code == 200:
                        data = resp.json()
                        console.print(f"[bold]{accession}[/bold]")
                        for k, v in data.items():
                            if k not in ("created_at", "updated_at"):
                                console.print(f"  {k}: {v}")
                        return
                console.print(f"[red]Not found: {accession}[/red]")
        finally:
            await client.close()

    anyio.run(_status)


def search(
    query: str = typer.Argument(..., help="Search query"),
) -> None:
    """Search samples and projects."""
    cfg = load_config(CONFIG_PATH)
    client = SeqDBClient(cfg)

    async def _search():
        try:
            resp = await client.get("/api/v1/search/", params={"q": query})
            resp.raise_for_status()
            results = resp.json()
            if not results:
                console.print("[yellow]No results found[/yellow]")
                return
            for r in results:
                console.print(f"  {r.get('accession', '?')} — {r.get('title', r.get('organism', ''))}")
        finally:
            await client.close()

    anyio.run(_search)
