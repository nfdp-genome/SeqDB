from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.archive_submission import ArchiveSubmissionResponse
from app.services.archive_tracking import ArchiveTrackingService

router = APIRouter(prefix="/archive-submissions", tags=["Archive Submissions"])


@router.get("/{entity_type}/{entity_accession}", response_model=list[ArchiveSubmissionResponse])
async def list_archive_submissions(
    entity_type: str, entity_accession: str,
    db: AsyncSession = Depends(get_db),
):
    svc = ArchiveTrackingService(db)
    subs = await svc.list_for_entity(entity_type, entity_accession)
    return subs
