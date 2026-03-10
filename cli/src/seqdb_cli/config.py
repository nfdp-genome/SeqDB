from __future__ import annotations

import sys
from dataclasses import dataclass, asdict
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib
import tomli_w

CONFIG_DIR = Path.home() / ".seqdb"
CONFIG_PATH = CONFIG_DIR / "config.toml"


@dataclass
class SeqDBConfig:
    server_url: str = ""
    access_token: str = ""
    refresh_token: str = ""


def load_config(path: Path = CONFIG_PATH) -> SeqDBConfig:
    if not path.exists():
        return SeqDBConfig()
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return SeqDBConfig(**{k: v for k, v in data.items() if k in SeqDBConfig.__dataclass_fields__})


def save_config(cfg: SeqDBConfig, path: Path = CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        tomli_w.dump(asdict(cfg), f)
