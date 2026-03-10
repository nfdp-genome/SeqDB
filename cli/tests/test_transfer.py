import httpx
import pytest
import respx
from pathlib import Path
from seqdb_cli.transfer import upload_files, download_files


@respx.mock
@pytest.mark.asyncio
async def test_upload_files(tmp_path):
    f1 = tmp_path / "read_R1.fastq.gz"
    f1.write_bytes(b"ACGT" * 100)

    respx.post("https://api.test/api/v1/staging/initiate").mock(
        return_value=httpx.Response(200, json={
            "staged_file_id": 1,
            "presigned_url": "https://minio.test/upload/read_R1.fastq.gz",
            "staging_path": "staging/user1/abc/read_R1.fastq.gz",
            "expires_in": 3600,
        })
    )
    respx.put("https://minio.test/upload/read_R1.fastq.gz").mock(
        return_value=httpx.Response(200)
    )
    respx.post("https://api.test/api/v1/staging/complete/1").mock(
        return_value=httpx.Response(200, json={
            "id": 1, "filename": "read_R1.fastq.gz", "file_size": 400,
            "checksum_md5": "abc", "upload_method": "browser",
            "status": "verified", "uploaded_at": "2026-01-01T00:00:00",
        })
    )

    results = await upload_files(
        base_url="https://api.test",
        token="tok",
        files=[f1],
        max_concurrent=2,
        show_progress=False,
    )
    assert len(results) == 1
    assert results[0]["staged_file_id"] == 1


@respx.mock
@pytest.mark.asyncio
async def test_download_files(tmp_path):
    respx.get("https://minio.test/file.fastq.gz").mock(
        return_value=httpx.Response(200, content=b"ACGT" * 50)
    )

    results = await download_files(
        urls=[("https://minio.test/file.fastq.gz", "sample_R1.fastq.gz")],
        output_dir=tmp_path,
        max_concurrent=2,
        show_progress=False,
    )
    assert len(results) == 1
    assert (tmp_path / "sample_R1.fastq.gz").exists()
