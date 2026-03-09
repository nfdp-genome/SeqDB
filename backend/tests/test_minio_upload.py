"""Integration test for MinIO upload flow. Requires running MinIO."""
import pytest
import httpx
from minio import Minio


MINIO_ENDPOINT = "localhost:9002"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"


def minio_available() -> bool:
    try:
        client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY,
                       secret_key=MINIO_SECRET_KEY, secure=False)
        client.list_buckets()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not minio_available(), reason="MinIO not running")
@pytest.mark.asyncio
async def test_full_upload_to_minio(client, auth_headers):
    # 1. Create project
    r = await client.post("/api/v1/projects", json={
        "title": "Upload Test Project",
        "description": "Testing real MinIO upload",
        "project_type": "WGS",
    }, headers=auth_headers)
    project_acc = r.json()["accession"]

    # 2. Create sample
    r = await client.post("/api/v1/samples", json={
        "project_accession": project_acc,
        "checklist_id": "ERC000055",
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "collection_date": "2026-03-01",
        "geographic_location": "Saudi Arabia:Riyadh",
    }, headers=auth_headers)
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
    exp_acc = r.json()["accession"]

    # 4. Initiate upload — get presigned URL
    r = await client.post("/api/v1/upload/initiate", json={
        "experiment_accession": exp_acc,
        "filename": "test_R1.fastq.gz",
        "file_size": 1024,
        "checksum_md5": "d8e8fca2dc0f896fd7cb4cb0031ba249",
        "file_type": "FASTQ",
    }, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    upload_id = data["upload_id"]
    presigned_url = data["presigned_url"]
    assert "nfdp-raw" in presigned_url

    # 5. PUT data to presigned URL (real MinIO upload)
    test_data = b"@SEQ_ID\nGATTACA\n+\n!!!!!!\n" * 40  # fake FASTQ
    async with httpx.AsyncClient() as http:
        put_r = await http.put(presigned_url, content=test_data)
    assert put_r.status_code == 200

    # 6. Complete upload
    r = await client.post("/api/v1/upload/complete", json={
        "upload_id": upload_id,
        "checksum_md5": "d8e8fca2dc0f896fd7cb4cb0031ba249",
    }, headers=auth_headers)
    assert r.status_code == 200
    result = r.json()
    assert result["run_accession"].startswith("NFDP-RUN-")
    assert result["status"] == "uploaded"

    # 7. Verify file exists in MinIO
    minio_client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY,
                         secret_key=MINIO_SECRET_KEY, secure=False)
    objects = list(minio_client.list_objects("nfdp-raw", recursive=True))
    filenames = [obj.object_name for obj in objects]
    assert any("test_R1.fastq.gz" in f for f in filenames)

    # 8. Verify run appears in API
    r = await client.get("/api/v1/runs")
    runs = r.json()
    assert len(runs) >= 1
    assert any(run["accession"] == result["run_accession"] for run in runs)
