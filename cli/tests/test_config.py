from pathlib import Path
from seqdb_cli.config import SeqDBConfig, load_config, save_config


def test_default_config():
    cfg = SeqDBConfig()
    assert cfg.server_url == ""
    assert cfg.access_token == ""
    assert cfg.refresh_token == ""


def test_save_and_load_config(tmp_path):
    config_path = tmp_path / "config.toml"
    cfg = SeqDBConfig(server_url="https://api.seqdb.example.com", access_token="tok123")
    save_config(cfg, config_path)
    loaded = load_config(config_path)
    assert loaded.server_url == "https://api.seqdb.example.com"
    assert loaded.access_token == "tok123"


def test_load_missing_config(tmp_path):
    config_path = tmp_path / "nonexistent.toml"
    cfg = load_config(config_path)
    assert cfg.server_url == ""
