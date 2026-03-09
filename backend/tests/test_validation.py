import pytest
from app.services.validation import validate_sample_metadata, list_checklists


def test_validate_farm_animal_valid():
    errors = validate_sample_metadata("ERC000055", {
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "collection_date": "2026-01-15",
        "geographic_location": "Saudi Arabia:Riyadh",
    })
    assert errors == []


def test_validate_farm_animal_missing_required():
    errors = validate_sample_metadata("ERC000055", {
        "organism": "Camelus dromedarius",
    })
    assert len(errors) > 0
    fields = [e["field"] for e in errors]
    assert "required" in fields or any("tax_id" in f for f in fields)


def test_validate_unknown_checklist():
    errors = validate_sample_metadata("UNKNOWN", {"organism": "test"})
    assert any("checklist" in e["message"].lower() for e in errors)


def test_validate_pathogen_valid():
    errors = validate_sample_metadata("ERC000020", {
        "organism": "Brucella melitensis",
        "tax_id": 29459,
        "collection_date": "2026-02-01",
        "geographic_location": "Saudi Arabia:Jeddah",
        "host": "Camelus dromedarius",
    })
    assert errors == []


def test_validate_pathogen_missing_host():
    errors = validate_sample_metadata("ERC000020", {
        "organism": "Brucella melitensis",
        "tax_id": 29459,
        "collection_date": "2026-02-01",
        "geographic_location": "Saudi Arabia:Jeddah",
    })
    assert len(errors) > 0


def test_list_checklists():
    checklists = list_checklists()
    assert len(checklists) >= 5
    ids = [c["id"] for c in checklists]
    assert "ERC000055" in ids
    assert "snpchip_livestock" in ids
