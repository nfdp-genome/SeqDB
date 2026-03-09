import pytest


@pytest.fixture
async def project_accession(client, auth_headers):
    response = await client.post("/api/v1/projects", json={
        "title": "Test Project",
        "description": "For sample tests",
        "project_type": "WGS",
    }, headers=auth_headers)
    return response.json()["accession"]


@pytest.mark.asyncio
async def test_create_sample(client, auth_headers, project_accession):
    response = await client.post("/api/v1/samples", json={
        "project_accession": project_accession,
        "checklist_id": "ERC000055",
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "collection_date": "2026-01-15",
        "geographic_location": "Saudi Arabia:Riyadh",
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["accession"].startswith("NFDP-SAM-")
    assert data["organism"] == "Camelus dromedarius"


@pytest.mark.asyncio
async def test_create_sample_invalid_project(client, auth_headers):
    response = await client.post("/api/v1/samples", json={
        "project_accession": "NFDP-PRJ-999999",
        "checklist_id": "ERC000055",
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "collection_date": "2026-01-15",
        "geographic_location": "Saudi Arabia:Riyadh",
    }, headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_samples(client, auth_headers, project_accession):
    await client.post("/api/v1/samples", json={
        "project_accession": project_accession,
        "checklist_id": "ERC000055",
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "collection_date": "2026-01-15",
        "geographic_location": "Saudi Arabia:Riyadh",
    }, headers=auth_headers)
    response = await client.get("/api/v1/samples")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_sample_not_found(client):
    response = await client.get("/api/v1/samples/NFDP-SAM-999999")
    assert response.status_code == 404
