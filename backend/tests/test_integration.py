import pytest


@pytest.mark.asyncio
async def test_full_deposition_workflow(client, auth_headers):
    # 1. Create project
    r = await client.post("/api/v1/projects", json={
        "title": "Integration Test Project",
        "description": "Testing full workflow",
        "project_type": "WGS",
    }, headers=auth_headers)
    assert r.status_code == 201
    project_acc = r.json()["accession"]
    assert project_acc.startswith("NFDP-PRJ-")

    # 2. Create sample
    r = await client.post("/api/v1/samples", json={
        "project_accession": project_acc,
        "checklist_id": "ERC000055",
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "collection_date": "2026-01-15",
        "geographic_location": "Saudi Arabia:Riyadh",
    }, headers=auth_headers)
    assert r.status_code == 201
    sample_acc = r.json()["accession"]

    # 3. Create experiment
    r = await client.post("/api/v1/experiments", json={
        "sample_accession": sample_acc,
        "platform": "ILLUMINA",
        "instrument_model": "NovaSeq 6000",
        "library_strategy": "WGS",
        "library_source": "GENOMIC",
        "library_layout": "PAIRED",
        "insert_size": 350,
    }, headers=auth_headers)
    assert r.status_code == 201

    # 4. Verify project lists correctly
    r = await client.get("/api/v1/projects")
    assert r.status_code == 200
    assert len(r.json()) == 1

    # 5. Verify project retrieval by accession
    r = await client.get(f"/api/v1/projects/{project_acc}")
    assert r.status_code == 200
    assert r.json()["title"] == "Integration Test Project"


@pytest.mark.asyncio
async def test_submission_validation_workflow(client, auth_headers):
    # 1. Create project
    r = await client.post("/api/v1/projects", json={
        "title": "Submission Validation Project",
        "description": "Testing submission validation",
        "project_type": "WGS",
    }, headers=auth_headers)
    assert r.status_code == 201
    project_acc = r.json()["accession"]

    # 2. Create sample with valid checklist metadata
    r = await client.post("/api/v1/samples", json={
        "project_accession": project_acc,
        "checklist_id": "ERC000011",
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "collection_date": "2026-02-01",
        "geographic_location": "Saudi Arabia:Jeddah",
    }, headers=auth_headers)
    assert r.status_code == 201
    sample_acc = r.json()["accession"]

    # 3. Create experiment
    r = await client.post("/api/v1/experiments", json={
        "sample_accession": sample_acc,
        "platform": "ILLUMINA",
        "instrument_model": "NextSeq 2000",
        "library_strategy": "WGS",
        "library_source": "GENOMIC",
        "library_layout": "PAIRED",
        "insert_size": 300,
    }, headers=auth_headers)
    assert r.status_code == 201

    # 4. Create submission (run_accessions required but empty since no runs uploaded)
    r = await client.post("/api/v1/submissions", json={
        "project_accession": project_acc,
        "title": "Test Submission",
        "run_accessions": [],
    }, headers=auth_headers)
    assert r.status_code == 201
    sub_acc = r.json()["submission_id"]
    assert sub_acc.startswith("NFDP-SUB-")
    assert r.json()["status"] == "draft"

    # 5. Validate submission
    r = await client.post(f"/api/v1/submissions/{sub_acc}/validate", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] in ("validated", "draft")


@pytest.mark.asyncio
async def test_search_across_entities(client, auth_headers):
    # Create project
    r = await client.post("/api/v1/projects", json={
        "title": "Arabian Oryx Genomics Project",
        "description": "Conservation genomics for Arabian Oryx",
        "project_type": "WGS",
    }, headers=auth_headers)
    assert r.status_code == 201

    # Search for it
    r = await client.get("/api/v1/search?q=Arabian+Oryx")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert any("Arabian Oryx" in result.get("title", "") for result in data["results"])


@pytest.mark.asyncio
async def test_checklist_validation_flow(client):
    # List available checklists
    r = await client.get("/api/v1/checklists")
    assert r.status_code == 200
    checklists = r.json()
    assert len(checklists) >= 5

    # Get schema for farm animal checklist
    r = await client.get("/api/v1/checklists/ERC000055/schema")
    assert r.status_code == 200
    schema = r.json()
    assert "organism" in schema["required"]

    # Verify SNP chip checklist exists
    checklist_ids = [c["id"] for c in checklists]
    assert "snpchip_livestock" in checklist_ids
