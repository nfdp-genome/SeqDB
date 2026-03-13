import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def project_with_data(client, auth_headers):
    """Create a project with sample and experiment for NCBI tests."""
    r = await client.post("/api/v1/projects", json={
        "title": "NCBI Test Project",
        "description": "Testing NCBI submission",
        "project_type": "WGS",
    }, headers=auth_headers)
    assert r.status_code == 201
    project_acc = r.json()["accession"]

    r = await client.post("/api/v1/samples", json={
        "project_accession": project_acc,
        "checklist_id": "ERC000011",
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "collection_date": "2026-01-15",
        "geographic_location": "Saudi Arabia:Riyadh",
        "domain_schema_id": "livestock",
    }, headers=auth_headers)
    assert r.status_code == 201
    sample_acc = r.json()["accession"]

    r = await client.post("/api/v1/experiments", json={
        "sample_accession": sample_acc,
        "platform": "ILLUMINA",
        "instrument_model": "NovaSeq 6000",
        "library_strategy": "WGS",
        "library_source": "GENOMIC",
        "library_layout": "PAIRED",
    }, headers=auth_headers)
    assert r.status_code == 201

    return project_acc


@pytest.mark.asyncio
async def test_ncbi_submit_no_config(client, auth_headers, project_with_data):
    """Submit should fail gracefully when NCBI is not configured."""
    response = await client.post(
        f"/api/v1/ncbi/submit/{project_with_data}",
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "not configured" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ncbi_submit_project_not_found(client, auth_headers):
    """Without NCBI configured, returns 400 before checking project existence."""
    response = await client.post(
        "/api/v1/ncbi/submit/NFDP-PRJ-999999",
        headers=auth_headers,
    )
    # Returns 400 because NCBI API key check happens first
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_ncbi_status_no_submissions(client, auth_headers, project_with_data):
    response = await client.get(
        f"/api/v1/ncbi/status/{project_with_data}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["submissions"] == []


@pytest.mark.asyncio
async def test_ncbi_submit_unauthorized(client, project_with_data):
    response = await client.post(
        f"/api/v1/ncbi/submit/{project_with_data}",
    )
    assert response.status_code in (401, 403)
