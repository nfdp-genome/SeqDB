"""Generic field mapper engine for domain schemas."""

from app.schemas.domains import get_domain_schema


def validate_sample(data: dict, domain_id: str) -> list[dict]:
    schema = get_domain_schema(domain_id)
    if schema is None:
        return [{"field": "domain", "message": f"Domain '{domain_id}' not found"}]

    errors = []
    fields = schema["fields"]

    for field_name, field_def in fields.items():
        value = data.get(field_name)
        required = field_def.get("required", False)

        if required and (value is None or value == ""):
            errors.append({"field": field_name, "message": f"Required field '{field_name}' is missing"})
            continue

        if value is None or value == "":
            continue

        field_type = field_def.get("type", "string")
        if field_type == "integer":
            if not isinstance(value, int):
                errors.append({"field": field_name, "message": f"Expected integer for '{field_name}'"})
        elif field_type == "enum":
            allowed = field_def.get("values", [])
            if value not in allowed:
                errors.append({
                    "field": field_name,
                    "message": f"Invalid value '{value}' for '{field_name}'. Allowed: {allowed}",
                })

    return errors


def export_ena(data: dict, domain_id: str) -> dict:
    return _export(data, domain_id, "ena")


def export_ncbi(data: dict, domain_id: str) -> dict:
    return _export(data, domain_id, "ncbi")


def _export(data: dict, domain_id: str, archive: str) -> dict:
    schema = get_domain_schema(domain_id)
    if schema is None:
        return {}

    result = {}
    fields = schema["fields"]

    for field_name, field_def in fields.items():
        value = data.get(field_name)
        if value is None:
            continue

        mapping = field_def.get(archive)
        if mapping is None:
            continue

        archive_name = mapping["name"]
        result[archive_name] = value

    return result


def get_template_columns(domain_id: str) -> list[str]:
    schema = get_domain_schema(domain_id)
    if schema is None:
        return []
    return list(schema["fields"].keys())
