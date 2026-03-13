from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.archive_submission import ArchiveSubmission
from app.models.enums import Archive, ArchiveSubmissionStatus


class ArchiveTrackingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, entity_type: str, entity_accession: str, archive: Archive) -> ArchiveSubmission:
        sub = ArchiveSubmission(
            entity_type=entity_type,
            entity_accession=entity_accession,
            archive=archive,
            status=ArchiveSubmissionStatus.DRAFT,
        )
        self.db.add(sub)
        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def list_for_entity(self, entity_type: str, entity_accession: str) -> list[ArchiveSubmission]:
        result = await self.db.execute(
            select(ArchiveSubmission).where(
                ArchiveSubmission.entity_type == entity_type,
                ArchiveSubmission.entity_accession == entity_accession,
            )
        )
        return list(result.scalars().all())

    async def update_status(
        self, submission_id: int, status: ArchiveSubmissionStatus,
        archive_accession: str | None = None, response_data: dict | None = None,
    ) -> ArchiveSubmission:
        result = await self.db.execute(
            select(ArchiveSubmission).where(ArchiveSubmission.id == submission_id)
        )
        sub = result.scalar_one()
        sub.status = status
        if archive_accession:
            sub.archive_accession = archive_accession
        if response_data:
            sub.response_data = response_data
        if status == ArchiveSubmissionStatus.SUBMITTED:
            sub.submitted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(sub)
        return sub
