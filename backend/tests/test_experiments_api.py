import pytest


@pytest.fixture
async def sample_accession(client, auth_headers):
    project_r = await client.post("/api/v1/projects", json={
        "title": "Test Project",
        "description": "For experiment tests",
        "project_type": "WGS",
    }, headers=auth_headers)
    project_acc = project_r.json()["accession"]

    sample_r = await client.post("/api/v1/samples", json={
        "project_accession": project_acc,
        "checklist_id": "ERC000055",
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "collection_date": "2026-01-15",
        "geographic_location": "Saudi Arabia:Riyadh",
    }, headers=auth_headers)
    return sample_r.json()["accession"]


@pytest.mark.asyncio
async def test_create_experiment(client, auth_headers, sample_accession):
    response = await client.post("/api/v1/experiments", json={
        "sample_accession": sample_accession,
        "platform": "ILLUMINA",
        "instrument_model": "NovaSeq 6000",
        "library_strategy": "WGS",
        "library_source": "GENOMIC",
        "library_layout": "PAIRED",
        "insert_size": 350,
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["accession"].startswith("NFDP-EXP-")
    assert data["platform"] == "ILLUMINA"


@pytest.mark.asyncio
async def test_create_experiment_invalid_sample(client, auth_headers):
    response = await client.post("/api/v1/experiments", json={
        "sample_accession": "NFDP-SAM-999999",
        "platform": "ILLUMINA",
        "instrument_model": "NovaSeq 6000",
        "library_strategy": "WGS",
        "library_source": "GENOMIC",
        "library_layout": "PAIRED",
    }, headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_experiment_not_found(client):
    response = await client.get("/api/v1/experiments/NFDP-EXP-999999")
    assert response.status_code == 404
