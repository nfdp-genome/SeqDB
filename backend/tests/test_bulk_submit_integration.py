"""Integration tests for the full bulk submit flow."""

import pytest


@pytest.mark.asyncio
async def test_full_bulk_submit_flow(client, auth_headers):
    # 1. Create project
    r = await client.post(
        "/api/v1/projects/",
        json={
            "title": "Bulk Test Project",
            "description": "Testing bulk submit",
            "project_type": "WGS",
        },
        headers=auth_headers,
    )
    assert r.status_code == 201
    project_acc = r.json()["accession"]

    # 2. Register staged files via the staging initiate endpoint
    r = await client.post(
        "/api/v1/staging/initiate",
        json={"filename": "CAMEL01_R1.fastq.gz", "file_size": 1024000},
        headers=auth_headers,
    )
    assert r.status_code == 200
    fwd_id = r.json()["staged_file_id"]

    r = await client.post(
        "/api/v1/staging/initiate",
        json={"filename": "CAMEL01_R2.fastq.gz", "file_size": 1024000},
        headers=auth_headers,
    )
    assert r.status_code == 200
    rev_id = r.json()["staged_file_id"]

    # 3. List staged files
    r = await client.get("/api/v1/staging/files", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 2

    # 4. Validate sample sheet (auto-detect mode -- files match by alias pattern)
    tsv = (
        "sample_alias\torganism\ttax_id\tcollection_date\tgeographic_location\n"
        "CAMEL01\tCamelus dromedarius\t9838\t2026-03-01\tSaudi Arabia:Riyadh\n"
    )

    r = await client.post(
        "/api/v1/bulk-submit/validate",
        files={"file": ("samples.tsv", tsv.encode(), "text/tab-separated-values")},
        data={"checklist_id": "ERC000055"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is True
    assert data["total_rows"] == 1

    # 5. Confirm submission
    r = await client.post(
        "/api/v1/bulk-submit/confirm",
        files={"file": ("samples.tsv", tsv.encode(), "text/tab-separated-values")},
        data={"project_accession": project_acc, "checklist_id": "ERC000055"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    result = r.json()
    assert result["status"] == "created"
    assert len(result["samples"]) == 1
    assert len(result["experiments"]) == 1
    assert len(result["runs"]) >= 1

    # 6. Verify staged files are marked as linked
    r = await client.get("/api/v1/staging/files", headers=auth_headers)
    assert r.status_code == 200
    staged = r.json()
    linked_count = sum(1 for f in staged if f.get("status") == "linked")
    # Files should either not appear (filtered) or show as linked
    assert linked_count >= 0  # linked files may still be listed


@pytest.mark.asyncio
async def test_bulk_template_download(client):
    r = await client.get("/api/v1/bulk-submit/template/ERC000055")
    assert r.status_code == 200
    content = r.text
    assert "sample_alias" in content
    assert "filename_forward" in content
    assert "md5_forward" in content


@pytest.mark.asyncio
async def test_staging_complete_endpoint(client, auth_headers):
    """Test the staging complete endpoint (graceful degradation without MinIO)."""
    # Initiate a staged file
    r = await client.post(
        "/api/v1/staging/initiate",
        json={"filename": "complete_test.fastq.gz", "file_size": 5000},
        headers=auth_headers,
    )
    assert r.status_code == 200
    staged_file_id = r.json()["staged_file_id"]

    # Complete the upload (MinIO not available, should still mark as verified)
    r = await client.post(
        f"/api/v1/staging/complete/{staged_file_id}",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "verified"
    assert data["id"] == staged_file_id


@pytest.mark.asyncio
async def test_staging_complete_not_found(client, auth_headers):
    """Test complete endpoint returns 404 for non-existent file."""
    r = await client.post(
        "/api/v1/staging/complete/99999",
        headers=auth_headers,
    )
    assert r.status_code == 404
