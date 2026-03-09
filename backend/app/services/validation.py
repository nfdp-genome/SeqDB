import json
from pathlib import Path

from jsonschema import Draft202012Validator

CHECKLISTS_DIR = Path(__file__).parent.parent / "plugins" / "checklists"


def load_checklist(checklist_id: str) -> dict | None:
    path = CHECKLISTS_DIR / f"{checklist_id}.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def list_checklists() -> list[dict]:
    results = []
    for path in CHECKLISTS_DIR.glob("*.json"):
        with open(path) as f:
            schema = json.load(f)
        results.append({
            "id": path.stem,
            "title": schema.get("title", path.stem),
            "required_fields": schema.get("required", []),
        })
    return results


def validate_sample_metadata(checklist_id: str, metadata: dict) -> list[dict]:
    schema = load_checklist(checklist_id)
    if schema is None:
        return [{"field": "checklist_id", "message": f"Checklist '{checklist_id}' not found"}]

    errors = []
    validator = Draft202012Validator(schema)
    for error in validator.iter_errors(metadata):
        field = ".".join(str(p) for p in error.absolute_path) or error.validator
        errors.append({"field": field, "message": error.message})
    return errors
