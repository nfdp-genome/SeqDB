import pytest


@pytest.fixture
async def experiment_accession(client, auth_headers):
    project_r = await client.post("/api/v1/projects", json={
        "title": "Upload Test Project",
        "description": "For upload tests",
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
    sample_acc = sample_r.json()["accession"]

    exp_r = await client.post("/api/v1/experiments", json={
        "sample_accession": sample_acc,
        "platform": "ILLUMINA",
        "instrument_model": "NovaSeq 6000",
        "library_strategy": "WGS",
        "library_source": "GENOMIC",
        "library_layout": "PAIRED",
        "insert_size": 350,
    }, headers=auth_headers)
    return exp_r.json()["accession"]


@pytest.mark.asyncio
async def test_initiate_upload(client, auth_headers, experiment_accession):
    response = await client.post("/api/v1/upload/initiate", json={
        "experiment_accession": experiment_accession,
        "filename": "sample_R1.fastq.gz",
        "file_size": 5368709120,
        "checksum_md5": "d41d8cd98f00b204e9800998ecf8427e",
        "file_type": "FASTQ",
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["upload_id"].startswith("up-")
    assert "presigned_url" in data
    assert data["expires_in"] == 86400


@pytest.mark.asyncio
async def test_complete_upload(client, auth_headers, experiment_accession):
    # Initiate
    init_r = await client.post("/api/v1/upload/initiate", json={
        "experiment_accession": experiment_accession,
        "filename": "sample_R1.fastq.gz",
        "file_size": 5368709120,
        "checksum_md5": "d41d8cd98f00b204e9800998ecf8427e",
        "file_type": "FASTQ",
    }, headers=auth_headers)
    upload_id = init_r.json()["upload_id"]

    # Complete
    response = await client.post("/api/v1/upload/complete", json={
        "upload_id": upload_id,
        "checksum_md5": "d41d8cd98f00b204e9800998ecf8427e",
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["run_accession"].startswith("NFDP-RUN-")
    assert data["status"] == "uploaded"


@pytest.mark.asyncio
async def test_complete_upload_checksum_mismatch(client, auth_headers, experiment_accession):
    init_r = await client.post("/api/v1/upload/initiate", json={
        "experiment_accession": experiment_accession,
        "filename": "sample_R1.fastq.gz",
        "file_size": 5368709120,
        "checksum_md5": "d41d8cd98f00b204e9800998ecf8427e",
        "file_type": "FASTQ",
    }, headers=auth_headers)
    upload_id = init_r.json()["upload_id"]

    response = await client.post("/api/v1/upload/complete", json={
        "upload_id": upload_id,
        "checksum_md5": "wrong_checksum_here",
    }, headers=auth_headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_initiate_upload_invalid_experiment(client, auth_headers):
    response = await client.post("/api/v1/upload/initiate", json={
        "experiment_accession": "NFDP-EXP-999999",
        "filename": "sample_R1.fastq.gz",
        "file_size": 1000,
        "checksum_md5": "abc123",
        "file_type": "FASTQ",
    }, headers=auth_headers)
    assert response.status_code == 404
