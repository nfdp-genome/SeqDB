import csv
import io
from app.services.validation import load_checklist, list_checklists


def generate_template_tsv(checklist_id: str) -> str | None:
    """Generate a TSV template with headers from a checklist schema."""
    schema = load_checklist(checklist_id)
    if schema is None:
        return None

    required = schema.get("required", [])
    optional = [
        k for k in schema.get("properties", {}).keys()
        if k not in required
    ]

    headers = required + optional
    output = io.StringIO()
    writer = csv.writer(output, delimiter="\t")
    writer.writerow(headers)

    # Write one example row with placeholders
    example = []
    props = schema.get("properties", {})
    for h in headers:
        prop = props.get(h, {})
        if "enum" in prop:
            example.append(prop["enum"][0])
        elif prop.get("type") == "integer":
            example.append("0")
        elif prop.get("format") == "date":
            example.append("2026-01-01")
        elif "pattern" in prop:
            example.append("Country:Region")
        else:
            example.append("")
    writer.writerow(example)

    return output.getvalue()


def parse_template_tsv(tsv_content: str) -> tuple[list[str], list[dict]]:
    """Parse uploaded TSV template into headers and rows."""
    reader = csv.DictReader(io.StringIO(tsv_content), delimiter="\t")
    headers = reader.fieldnames or []
    rows = list(reader)
    return headers, rows
