import httpx
import respx
from typer.testing import CliRunner
from seqdb_cli.main import app

runner = CliRunner()


def _setup_config(monkeypatch, tmp_path):
    from seqdb_cli.config import SeqDBConfig, save_config
    cfg_path = tmp_path / "config.toml"
    save_config(
        SeqDBConfig(server_url="https://api.test", access_token="tok"),
        cfg_path,
    )
    monkeypatch.setattr("seqdb_cli.commands.submit.CONFIG_PATH", cfg_path)
    return cfg_path


@respx.mock
def test_template_command(tmp_path, monkeypatch):
    _setup_config(monkeypatch, tmp_path)
    respx.get("https://api.test/api/v1/bulk-submit/template/ERC000011").mock(
        return_value=httpx.Response(
            200,
            content=b"sample_alias\torganism\ttax_id\n",
            headers={"content-type": "text/tab-separated-values"},
        )
    )
    result = runner.invoke(app, ["template", "ERC000011", "--output", str(tmp_path / "tmpl.tsv")])
    assert result.exit_code == 0
    assert (tmp_path / "tmpl.tsv").exists()


@respx.mock
def test_validate_command(tmp_path, monkeypatch):
    _setup_config(monkeypatch, tmp_path)
    sheet = tmp_path / "sheet.tsv"
    sheet.write_text("sample_alias\torganism\nSAM1\tBos taurus\n")
    respx.post("https://api.test/api/v1/bulk-submit/validate").mock(
        return_value=httpx.Response(200, json={
            "valid": True,
            "rows": [{"row_num": 1, "sample_alias": "SAM1", "errors": [], "warnings": []}],
            "errors": [],
        })
    )
    result = runner.invoke(app, ["validate", str(sheet), "--checklist", "ERC000011"])
    assert result.exit_code == 0
    assert "valid" in result.output.lower() or "Valid" in result.output or "passed" in result.output.lower()
