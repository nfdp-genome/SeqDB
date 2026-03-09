import pytest
from app.services.templates import generate_template_tsv, parse_template_tsv


def test_generate_template_farm_animal():
    tsv = generate_template_tsv("ERC000055")
    assert tsv is not None
    lines = tsv.strip().split("\n")
    headers = lines[0].split("\t")
    assert "organism" in headers
    assert "tax_id" in headers
    assert "collection_date" in headers
    assert "geographic_location" in headers
    # Second line is example row
    assert len(lines) == 2


def test_generate_template_unknown():
    tsv = generate_template_tsv("UNKNOWN_CHECKLIST")
    assert tsv is None


def test_generate_template_pathogen():
    tsv = generate_template_tsv("ERC000020")
    assert tsv is not None
    headers = tsv.strip().split("\n")[0].split("\t")
    assert "host" in headers


def test_parse_template_tsv():
    tsv = "organism\ttax_id\tcollection_date\tgeographic_location\nCamelus dromedarius\t9838\t2026-01-15\tSaudi Arabia:Riyadh\n"
    headers, rows = parse_template_tsv(tsv)
    assert headers == ["organism", "tax_id", "collection_date", "geographic_location"]
    assert len(rows) == 1
    assert rows[0]["organism"] == "Camelus dromedarius"


def test_generate_template_snpchip():
    tsv = generate_template_tsv("snpchip_livestock")
    assert tsv is not None
    headers = tsv.strip().split("\n")[0].split("\t")
    assert "organism" in headers
    assert "chip_type" in headers


@pytest.mark.asyncio
async def test_download_template_endpoint(client):
    response = await client.get("/api/v1/templates/ERC000055/download")
    assert response.status_code == 200
    assert "text/tab-separated-values" in response.headers["content-type"]
    content = response.text
    assert "organism" in content
    assert "tax_id" in content


@pytest.mark.asyncio
async def test_download_template_not_found(client):
    response = await client.get("/api/v1/templates/UNKNOWN/download")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_upload_template_valid(client, auth_headers):
    # First create a project
    r = await client.post("/api/v1/projects", json={
        "title": "Template Upload Test",
        "description": "Testing template upload",
        "project_type": "WGS",
    }, headers=auth_headers)
    project_acc = r.json()["accession"]

    tsv = "organism\ttax_id\tcollection_date\tgeographic_location\nOvis aries\t9940\t2026-03-01\tSaudi Arabia:Tabuk\nCapra hircus\t9925\t2026-03-02\tSaudi Arabia:AlUla\n"

    r = await client.post("/api/v1/templates/upload",
        files={"file": ("samples.tsv", tsv.encode(), "text/tab-separated-values")},
        data={"project_accession": project_acc, "checklist_id": "ERC000055"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "created"
    assert data["created"] == 2


@pytest.mark.asyncio
async def test_upload_template_validation_failure(client, auth_headers):
    r = await client.post("/api/v1/projects", json={
        "title": "Template Validation Test",
        "description": "Testing validation",
        "project_type": "WGS",
    }, headers=auth_headers)
    project_acc = r.json()["accession"]

    # Missing required field: tax_id
    tsv = "organism\tcollection_date\tgeographic_location\nOvis aries\t2026-03-01\tSaudi Arabia:Tabuk\n"

    r = await client.post("/api/v1/templates/upload",
        files={"file": ("bad.tsv", tsv.encode(), "text/tab-separated-values")},
        data={"project_accession": project_acc, "checklist_id": "ERC000055"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "validation_failed"
    assert data["error_rows"] >= 1
