from __future__ import annotations

import anyio
import typer
from rich.console import Console

from seqdb_cli.client import SeqDBClient
from seqdb_cli.config import CONFIG_PATH, SeqDBConfig, load_config, save_config

auth_app = typer.Typer(name="auth", hidden=True)
console = Console()


def login(
    url: str = typer.Option(..., "--url", help="SeqDB server URL"),
    email: str = typer.Option(..., "--email", help="Account email"),
    password: str = typer.Option(..., "--password", prompt=True, hide_input=True, help="Password"),
) -> None:
    """Authenticate with a SeqDB server."""
    cfg = SeqDBConfig(server_url=url)
    client = SeqDBClient(cfg)

    async def _login():
        try:
            tokens = await client.login(email, password)
            cfg.access_token = tokens["access_token"]
            cfg.refresh_token = tokens.get("refresh_token", "")
            save_config(cfg, CONFIG_PATH)
            console.print(f"[green]Logged in[/green] to {url}")
        finally:
            await client.close()

    anyio.run(_login)


def logout() -> None:
    """Clear stored credentials."""
    cfg = load_config()
    cfg.access_token = ""
    cfg.refresh_token = ""
    save_config(cfg, CONFIG_PATH)
    console.print("[yellow]Logged out[/yellow]. Credentials cleared.")
