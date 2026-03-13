from pathlib import Path
from functools import lru_cache

import yaml

_DOMAINS_DIR = Path(__file__).parent


@lru_cache
def _load_all_schemas() -> dict[str, dict]:
    schemas = {}
    for path in _DOMAINS_DIR.glob("*.yaml"):
        with open(path) as f:
            schema = yaml.safe_load(f)
        schemas[schema["domain"]] = schema
    return schemas


def list_domains() -> list[dict]:
    return [
        {
            "domain": s["domain"],
            "display_name": s["display_name"],
            "ena_checklist": s["ena_checklist"],
            "ncbi_package": s["ncbi_package"],
        }
        for s in _load_all_schemas().values()
    ]


def get_domain_schema(domain_id: str) -> dict | None:
    return _load_all_schemas().get(domain_id)
