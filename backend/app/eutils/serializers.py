"""JSON and XML response serializers for E-utilities endpoints."""

from xml.etree.ElementTree import Element, SubElement, tostring
from datetime import date, datetime


def serialize_esearch_json(result: dict, db: str) -> dict:
    """Format esearch results as NCBI-style JSON."""
    return {
        "header": {"type": "esearch", "version": "0.3"},
        "esearchresult": {
            "db": db,
            "count": str(result["count"]),
            "retmax": str(result["retmax"]),
            "retstart": str(result["retstart"]),
            "idlist": result["ids"],
        },
    }


def serialize_esearch_xml(result: dict, db: str) -> str:
    """Format esearch results as NCBI-style XML."""
    root = Element("eSearchResult")
    SubElement(root, "Count").text = str(result["count"])
    SubElement(root, "RetMax").text = str(result["retmax"])
    SubElement(root, "RetStart").text = str(result["retstart"])
    id_list = SubElement(root, "IdList")
    for acc in result["ids"]:
        SubElement(id_list, "Id").text = acc
    return tostring(root, encoding="unicode", xml_declaration=True)


def serialize_efetch_json(records: list[dict], db: str) -> dict:
    """Format efetch results as JSON."""
    return {
        "header": {"type": "efetch", "version": "0.3"},
        "db": db,
        "count": len(records),
        "records": records,
    }


def serialize_efetch_xml(records: list[dict], db: str) -> str:
    """Format efetch results as NCBI-compatible XML."""
    root = Element("RecordSet", db=db)
    for record in records:
        rec_elem = SubElement(root, "Record")
        for key, value in record.items():
            if value is None:
                continue
            elem = SubElement(rec_elem, key)
            if isinstance(value, (date, datetime)):
                elem.text = value.isoformat()
            else:
                elem.text = str(value)
    return tostring(root, encoding="unicode", xml_declaration=True)


def serialize_esummary_json(records: list[dict], db: str) -> dict:
    """Format esummary results as JSON (lighter than efetch)."""
    summary_fields = {
        "bioproject": ["internal_accession", "title", "description",
                       "project_type", "created_at", "ncbi_accession"],
        "biosample": ["internal_accession", "organism", "tax_id", "breed",
                      "geographic_location", "created_at", "ncbi_accession"],
        "sra": ["internal_accession", "platform", "instrument_model",
                "library_strategy", "created_at", "ncbi_accession"],
    }
    fields = summary_fields.get(db, list(records[0].keys()) if records else [])

    summaries = []
    for record in records:
        summary = {k: record.get(k) for k in fields if k in record}
        summaries.append(summary)

    return {
        "header": {"type": "esummary", "version": "0.3"},
        "db": db,
        "result": summaries,
    }


def serialize_esummary_xml(records: list[dict], db: str) -> str:
    """Format esummary results as XML."""
    root = Element("eSummaryResult")
    summary_fields = {
        "bioproject": ["internal_accession", "title", "project_type", "created_at"],
        "biosample": ["internal_accession", "organism", "tax_id", "breed", "created_at"],
        "sra": ["internal_accession", "platform", "instrument_model", "created_at"],
    }
    fields = summary_fields.get(db, [])

    for record in records:
        doc = SubElement(root, "DocumentSummary")
        for key in fields:
            val = record.get(key)
            if val is None:
                continue
            item = SubElement(doc, "Item", Name=key)
            item.text = str(val)

    return tostring(root, encoding="unicode", xml_declaration=True)


def serialize_einfo_json(databases: list[dict]) -> dict:
    """Format einfo results as JSON."""
    return {
        "header": {"type": "einfo", "version": "0.3"},
        "einforesult": {
            "dblist": [d["name"] for d in databases],
            "databases": databases,
        },
    }


def serialize_einfo_xml(databases: list[dict]) -> str:
    """Format einfo results as XML."""
    root = Element("eInfoResult")
    db_list = SubElement(root, "DbList")
    for db in databases:
        db_elem = SubElement(db_list, "DbName")
        db_elem.text = db["name"]
    return tostring(root, encoding="unicode", xml_declaration=True)
