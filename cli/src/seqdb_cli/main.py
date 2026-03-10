import typer
from seqdb_cli.commands.auth import login, logout
from seqdb_cli.commands.submit import template, upload, validate, submit
from seqdb_cli.commands.fetch import fetch
from seqdb_cli.commands.ingest import ingest
from seqdb_cli.commands.status import status, search

app = typer.Typer(
    name="seqdb",
    help="SeqDB — genomic data submission, retrieval, and pipeline integration.",
    no_args_is_help=True,
)

app.command()(login)
app.command()(logout)
app.command()(template)
app.command()(upload)
app.command()(validate)
app.command()(submit)
app.command()(fetch)
app.command()(ingest)
app.command()(status)
app.command()(search)


@app.callback()
def main():
    """SeqDB CLI for genomic data management."""


if __name__ == "__main__":
    app()
