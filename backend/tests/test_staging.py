import pytest
import pytest_asyncio

from app.models.enums import UploadMethod, StagedFileStatus
from app.services.staging import StagingService


@pytest.mark.asyncio
async def test_list_staged_files_empty(db, test_user):
    svc = StagingService(db)
    files = await svc.list_files(test_user.id)
    assert files == []


@pytest.mark.asyncio
async def test_register_staged_file(db, test_user):
    svc = StagingService(db)
    staged = await svc.register_file(
        user_id=test_user.id,
        filename="sample_R1.fastq.gz",
        file_size=1024000,
        checksum_md5="d41d8cd98f00b204e9800998ecf8427e",
        upload_method=UploadMethod.BROWSER,
        staging_path="staging/1/abc123/sample_R1.fastq.gz",
    )
    assert staged.id is not None
    assert staged.filename == "sample_R1.fastq.gz"
    assert staged.status == StagedFileStatus.PENDING
    assert staged.file_size == 1024000

    files = await svc.list_files(test_user.id)
    assert len(files) == 1
    assert files[0].id == staged.id


@pytest.mark.asyncio
async def test_delete_staged_file(db, test_user):
    svc = StagingService(db)
    staged = await svc.register_file(
        user_id=test_user.id,
        filename="to_delete.fastq.gz",
        file_size=500,
        checksum_md5="a" * 32,
        upload_method=UploadMethod.FTP,
        staging_path="staging/1/xyz/to_delete.fastq.gz",
    )

    deleted = await svc.delete_file(staged.id, test_user.id)
    assert deleted is True

    files = await svc.list_files(test_user.id)
    assert len(files) == 0

    # Deleting again returns False
    deleted_again = await svc.delete_file(staged.id, test_user.id)
    assert deleted_again is False


@pytest.mark.asyncio
async def test_find_files_by_alias(db, test_user):
    svc = StagingService(db)

    # Register files with alias pattern
    await svc.register_file(
        user_id=test_user.id,
        filename="SAMPLE01_R1.fastq.gz",
        file_size=1000,
        checksum_md5="b" * 32,
        upload_method=UploadMethod.BROWSER,
        staging_path="staging/1/a/SAMPLE01_R1.fastq.gz",
    )
    await svc.register_file(
        user_id=test_user.id,
        filename="SAMPLE01_R2.fastq.gz",
        file_size=1000,
        checksum_md5="c" * 32,
        upload_method=UploadMethod.BROWSER,
        staging_path="staging/1/b/SAMPLE01_R2.fastq.gz",
    )
    # A file that should NOT match
    await svc.register_file(
        user_id=test_user.id,
        filename="SAMPLE02_R1.fastq.gz",
        file_size=1000,
        checksum_md5="d" * 32,
        upload_method=UploadMethod.BROWSER,
        staging_path="staging/1/c/SAMPLE02_R1.fastq.gz",
    )

    matches = await svc.find_by_alias("SAMPLE01", test_user.id)
    assert len(matches) == 2
    filenames = {m.filename for m in matches}
    assert filenames == {"SAMPLE01_R1.fastq.gz", "SAMPLE01_R2.fastq.gz"}


@pytest.mark.asyncio
async def test_find_by_filename(db, test_user):
    svc = StagingService(db)
    await svc.register_file(
        user_id=test_user.id,
        filename="unique_file.fastq.gz",
        file_size=2000,
        checksum_md5="e" * 32,
        upload_method=UploadMethod.BROWSER,
        staging_path="staging/1/d/unique_file.fastq.gz",
    )

    found = await svc.find_by_filename("unique_file.fastq.gz", test_user.id)
    assert found is not None
    assert found.filename == "unique_file.fastq.gz"

    not_found = await svc.find_by_filename("nonexistent.fastq.gz", test_user.id)
    assert not_found is None


@pytest.mark.asyncio
async def test_mark_linked(db, test_user):
    svc = StagingService(db)
    s1 = await svc.register_file(
        user_id=test_user.id,
        filename="link1.fastq.gz",
        file_size=100,
        checksum_md5="f" * 32,
        upload_method=UploadMethod.BROWSER,
        staging_path="staging/1/e/link1.fastq.gz",
    )
    s2 = await svc.register_file(
        user_id=test_user.id,
        filename="link2.fastq.gz",
        file_size=200,
        checksum_md5="0" * 32,
        upload_method=UploadMethod.BROWSER,
        staging_path="staging/1/f/link2.fastq.gz",
    )

    await svc.mark_linked([s1.id, s2.id])

    await db.refresh(s1)
    await db.refresh(s2)
    assert s1.status == StagedFileStatus.LINKED
    assert s2.status == StagedFileStatus.LINKED


@pytest.mark.asyncio
async def test_staging_api_initiate(client, test_user, auth_headers):
    resp = await client.post(
        "/api/v1/staging/initiate",
        json={"filename": "test.fastq.gz", "file_size": 5000},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "staged_file_id" in data
    assert "presigned_url" in data
    assert "staging_path" in data
    assert data["expires_in"] == 86400


@pytest.mark.asyncio
async def test_staging_api_list_and_delete(client, test_user, auth_headers):
    # Initiate a file
    resp = await client.post(
        "/api/v1/staging/initiate",
        json={"filename": "list_test.fastq.gz", "file_size": 3000},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    file_id = resp.json()["staged_file_id"]

    # List files
    resp = await client.get("/api/v1/staging/files", headers=auth_headers)
    assert resp.status_code == 200
    files = resp.json()
    assert len(files) >= 1
    assert any(f["id"] == file_id for f in files)

    # Delete file
    resp = await client.delete(f"/api/v1/staging/files/{file_id}", headers=auth_headers)
    assert resp.status_code == 200

    # Verify deleted
    resp = await client.get("/api/v1/staging/files", headers=auth_headers)
    assert resp.status_code == 200
    files = resp.json()
    assert not any(f["id"] == file_id for f in files)


@pytest.mark.asyncio
async def test_staging_api_delete_not_found(client, test_user, auth_headers):
    resp = await client.delete("/api/v1/staging/files/99999", headers=auth_headers)
    assert resp.status_code == 404
