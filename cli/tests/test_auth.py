import httpx
import respx
from typer.testing import CliRunner
from seqdb_cli.main import app

runner = CliRunner()


@respx.mock
def test_login_command(tmp_path, monkeypatch):
    monkeypatch.setattr("seqdb_cli.commands.auth.CONFIG_PATH", tmp_path / "config.toml")
    respx.post("https://api.seqdb.test/api/v1/auth/login").mock(
        return_value=httpx.Response(200, json={
            "access_token": "tok-abc",
            "refresh_token": "ref-xyz",
            "token_type": "bearer",
            "expires_in": 3600,
        })
    )
    result = runner.invoke(app, [
        "login",
        "--url", "https://api.seqdb.test",
        "--email", "user@test.com",
        "--password", "secret",
    ])
    assert result.exit_code == 0
    assert "Logged in" in result.output


def test_logout_command(tmp_path, monkeypatch):
    monkeypatch.setattr("seqdb_cli.commands.auth.CONFIG_PATH", tmp_path / "config.toml")
    from seqdb_cli.config import SeqDBConfig, save_config
    save_config(
        SeqDBConfig(server_url="https://x.com", access_token="tok"),
        tmp_path / "config.toml",
    )
    result = runner.invoke(app, ["logout"])
    assert result.exit_code == 0
    assert "Logged out" in result.output
