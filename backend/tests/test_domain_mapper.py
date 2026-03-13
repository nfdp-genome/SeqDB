import pytest
from app.schemas.domains import list_domains, get_domain_schema
from app.schemas.domains.mapper import (
    validate_sample,
    export_ena,
    export_ncbi,
    get_template_columns,
)


def test_list_domains_returns_all_three():
    domains = list_domains()
    ids = {d["domain"] for d in domains}
    assert ids == {"livestock", "microbe", "environmental"}


def test_get_domain_schema_livestock():
    schema = get_domain_schema("livestock")
    assert schema is not None
    assert schema["domain"] == "livestock"
    assert schema["ena_checklist"] == "ERC000011"
    assert schema["ncbi_package"] == "Model.organism.animal.1.0"
    assert "organism" in schema["fields"]
    assert schema["fields"]["organism"]["required"] is True


def test_get_domain_schema_not_found():
    schema = get_domain_schema("nonexistent")
    assert schema is None


def test_validate_sample_valid_livestock():
    data = {
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "collection_date": "2026-01-15",
        "geographic_location": "Saudi Arabia:Riyadh",
    }
    errors = validate_sample(data, "livestock")
    assert errors == []


def test_validate_sample_missing_required():
    data = {"organism": "Camelus dromedarius"}
    errors = validate_sample(data, "livestock")
    field_names = {e["field"] for e in errors}
    assert "tax_id" in field_names
    assert "collection_date" in field_names
    assert "geographic_location" in field_names


def test_validate_sample_invalid_enum():
    data = {
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "collection_date": "2026-01-15",
        "geographic_location": "Saudi Arabia:Riyadh",
        "sex": "invalid_value",
    }
    errors = validate_sample(data, "livestock")
    assert len(errors) == 1
    assert errors[0]["field"] == "sex"


def test_validate_sample_unknown_domain():
    errors = validate_sample({}, "nonexistent")
    assert len(errors) == 1
    assert "not found" in errors[0]["message"]


def test_export_ena_livestock():
    data = {
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "geographic_location": "Saudi Arabia:Riyadh",
        "collection_date": "2026-01-15",
    }
    result = export_ena(data, "livestock")
    assert result["organism"] == "Camelus dromedarius"
    assert result["geographic_location_(country_and/or_sea)"] == "Saudi Arabia:Riyadh"
    assert "geographic_location" not in result


def test_export_ncbi_livestock():
    data = {
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "geographic_location": "Saudi Arabia:Riyadh",
        "collection_date": "2026-01-15",
    }
    result = export_ncbi(data, "livestock")
    assert result["organism"] == "Camelus dromedarius"
    assert result["geo_loc_name"] == "Saudi Arabia:Riyadh"
    assert "geographic_location" not in result


def test_get_template_columns_livestock():
    cols = get_template_columns("livestock")
    assert "organism" in cols
    assert "tax_id" in cols
    assert "collection_date" in cols
    assert "geographic_location" in cols


def test_get_template_columns_unknown_domain():
    cols = get_template_columns("nonexistent")
    assert cols == []
