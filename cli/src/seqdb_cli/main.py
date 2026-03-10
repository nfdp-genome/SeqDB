import typer

app = typer.Typer(
    name="seqdb",
    help="SeqDB — genomic data submission, retrieval, and pipeline integration.",
    no_args_is_help=True,
)


@app.callback()
def main():
    """SeqDB CLI for genomic data management."""


if __name__ == "__main__":
    app()
