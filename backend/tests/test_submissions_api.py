import pytest


@pytest.fixture
async def project_with_sample(client, auth_headers):
    project_r = await client.post("/api/v1/projects", json={
        "title": "Submission Test",
        "description": "For submission tests",
        "project_type": "WGS",
    }, headers=auth_headers)
    project_acc = project_r.json()["accession"]

    await client.post("/api/v1/samples", json={
        "project_accession": project_acc,
        "checklist_id": "ERC000055",
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "collection_date": "2026-01-15",
        "geographic_location": "Saudi Arabia:Riyadh",
    }, headers=auth_headers)
    return project_acc


@pytest.mark.asyncio
async def test_create_submission(client, auth_headers, project_with_sample):
    response = await client.post("/api/v1/submissions", json={
        "title": "Test batch",
        "project_accession": project_with_sample,
        "run_accessions": [],
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["submission_id"].startswith("NFDP-SUB-")
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_validate_submission(client, auth_headers, project_with_sample):
    sub_r = await client.post("/api/v1/submissions", json={
        "title": "Validate test",
        "project_accession": project_with_sample,
        "run_accessions": [],
    }, headers=auth_headers)
    sub_acc = sub_r.json()["submission_id"]

    response = await client.post(
        f"/api/v1/submissions/{sub_acc}/validate", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "validated"
    assert data["errors"] == []


@pytest.mark.asyncio
async def test_get_submission_not_found(client):
    response = await client.get("/api/v1/submissions/NFDP-SUB-999999")
    assert response.status_code == 404
