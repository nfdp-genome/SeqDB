import pytest
from app.services.archive_tracking import ArchiveTrackingService
from app.models.enums import Archive, ArchiveSubmissionStatus


@pytest.mark.asyncio
async def test_create_archive_submission_via_service(db):
    svc = ArchiveTrackingService(db)
    sub = await svc.create("sample", "NFDP-SAM-000001", Archive.NCBI)
    assert sub.id is not None
    assert sub.status == ArchiveSubmissionStatus.DRAFT


@pytest.mark.asyncio
async def test_list_submissions_for_entity(db):
    svc = ArchiveTrackingService(db)
    await svc.create("sample", "NFDP-SAM-000001", Archive.NCBI)
    await svc.create("sample", "NFDP-SAM-000001", Archive.ENA)
    subs = await svc.list_for_entity("sample", "NFDP-SAM-000001")
    assert len(subs) == 2
    archives = {s.archive for s in subs}
    assert archives == {Archive.NCBI, Archive.ENA}


@pytest.mark.asyncio
async def test_update_submission_status(db):
    svc = ArchiveTrackingService(db)
    sub = await svc.create("sample", "NFDP-SAM-000001", Archive.NCBI)
    updated = await svc.update_status(sub.id, ArchiveSubmissionStatus.SUBMITTED, archive_accession="SAMN12345")
    assert updated.status == ArchiveSubmissionStatus.SUBMITTED
    assert updated.archive_accession == "SAMN12345"


@pytest.mark.asyncio
async def test_archive_submissions_api(client, auth_headers, db):
    svc = ArchiveTrackingService(db)
    await svc.create("sample", "NFDP-SAM-000001", Archive.NCBI)
    response = await client.get("/api/v1/archive-submissions/sample/NFDP-SAM-000001")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["archive"] == "NCBI"
    assert data[0]["status"] == "draft"
