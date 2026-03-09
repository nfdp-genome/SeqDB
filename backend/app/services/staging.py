import uuid
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.staged_file import StagedFile
from app.models.enums import UploadMethod, StagedFileStatus
from app.services.storage import StorageService


BUCKET_STAGING = "nfdp-staging"


class StagingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_file(
        self,
        user_id: int,
        filename: str,
        file_size: int,
        checksum_md5: str,
        upload_method: UploadMethod,
        staging_path: str,
    ) -> StagedFile:
        staged = StagedFile(
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            checksum_md5=checksum_md5,
            upload_method=upload_method,
            staging_path=staging_path,
            status=StagedFileStatus.PENDING,
        )
        self.db.add(staged)
        await self.db.commit()
        await self.db.refresh(staged)
        return staged

    async def list_files(self, user_id: int) -> list[StagedFile]:
        result = await self.db.execute(
            select(StagedFile)
            .where(StagedFile.user_id == user_id)
            .where(StagedFile.status != StagedFileStatus.EXPIRED)
            .order_by(StagedFile.uploaded_at.desc())
        )
        return list(result.scalars().all())

    async def delete_file(self, file_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            select(StagedFile)
            .where(StagedFile.id == file_id)
            .where(StagedFile.user_id == user_id)
        )
        staged = result.scalar_one_or_none()
        if not staged:
            return False
        await self.db.delete(staged)
        await self.db.commit()
        return True

    async def find_by_alias(self, alias: str, user_id: int) -> list[StagedFile]:
        """Find staged files matching `{alias}_*` pattern for a user."""
        result = await self.db.execute(
            select(StagedFile)
            .where(StagedFile.user_id == user_id)
            .where(StagedFile.filename.like(f"{alias}_%"))
            .where(StagedFile.status != StagedFileStatus.EXPIRED)
        )
        return list(result.scalars().all())

    async def find_by_filename(self, filename: str, user_id: int) -> StagedFile | None:
        result = await self.db.execute(
            select(StagedFile)
            .where(StagedFile.user_id == user_id)
            .where(StagedFile.filename == filename)
            .where(StagedFile.status != StagedFileStatus.EXPIRED)
        )
        return result.scalar_one_or_none()

    async def mark_linked(self, file_ids: list[int]) -> None:
        if not file_ids:
            return
        await self.db.execute(
            update(StagedFile)
            .where(StagedFile.id.in_(file_ids))
            .values(status=StagedFileStatus.LINKED)
        )
        await self.db.commit()

    def generate_presigned_upload_url(
        self, user_id: int, filename: str
    ) -> tuple[str, str]:
        """Generate a staging path and presigned upload URL.

        Returns (staging_path, presigned_url).
        """
        unique_id = uuid.uuid4().hex[:12]
        staging_path = f"staging/{user_id}/{unique_id}/{filename}"

        try:
            storage = StorageService()
            storage.ensure_buckets()
            presigned_url = storage.generate_presigned_upload_url(
                BUCKET_STAGING, staging_path, expires_hours=24
            )
        except Exception:
            # Fallback if MinIO is unreachable (e.g., tests)
            presigned_url = (
                f"http://{settings.minio_endpoint}/{BUCKET_STAGING}/{staging_path}"
            )

        return staging_path, presigned_url
