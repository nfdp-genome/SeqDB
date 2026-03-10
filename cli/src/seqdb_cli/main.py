import typer
from seqdb_cli.commands.auth import login, logout

app = typer.Typer(
    name="seqdb",
    help="SeqDB — genomic data submission, retrieval, and pipeline integration.",
    no_args_is_help=True,
)

app.command()(login)
app.command()(logout)


@app.callback()
def main():
    """SeqDB CLI for genomic data management."""


if __name__ == "__main__":
    app()
