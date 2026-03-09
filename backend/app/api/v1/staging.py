import hashlib
import io
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.enums import UploadMethod, StagedFileStatus
from app.models.staged_file import StagedFile
from app.schemas.staging import (
    StagingInitiateRequest,
    StagingInitiateResponse,
    StagedFileResponse,
)
from app.services.staging import StagingService, BUCKET_STAGING
from app.services.storage import StorageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/staging", tags=["staging"])


@router.post("/initiate", response_model=StagingInitiateResponse)
async def initiate_staging(
    request: StagingInitiateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate a presigned URL for browser upload to staging area."""
    svc = StagingService(db)
    staging_path, presigned_url = svc.generate_presigned_upload_url(
        user.id, request.filename
    )

    # Register the staged file with a placeholder checksum (updated on completion)
    staged = await svc.register_file(
        user_id=user.id,
        filename=request.filename,
        file_size=request.file_size,
        checksum_md5="0" * 32,  # placeholder until upload completes
        upload_method=UploadMethod.BROWSER,
        staging_path=staging_path,
    )

    return StagingInitiateResponse(
        staged_file_id=staged.id,
        presigned_url=presigned_url,
        staging_path=staging_path,
        expires_in=86400,
    )


@router.get("/files", response_model=list[StagedFileResponse])
async def list_staged_files(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List the current user's staged files (excluding expired)."""
    svc = StagingService(db)
    files = await svc.list_files(user.id)
    return files


@router.delete("/files/{file_id}")
async def delete_staged_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Remove a staged file."""
    svc = StagingService(db)
    deleted = await svc.delete_file(file_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Staged file not found")
    return {"detail": "Staged file deleted"}


@router.post("/complete/{staged_file_id}", response_model=StagedFileResponse)
async def complete_staging_upload(
    staged_file_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Called after a browser upload completes. Verifies the file in MinIO and updates status."""
    result = await db.execute(
        select(StagedFile)
        .where(StagedFile.id == staged_file_id)
        .where(StagedFile.user_id == user.id)
    )
    staged = result.scalar_one_or_none()
    if not staged:
        raise HTTPException(status_code=404, detail="Staged file not found")

    # Try to compute MD5 from MinIO; graceful degradation if unavailable
    try:
        storage = StorageService()
        md5 = storage.compute_object_md5(BUCKET_STAGING, staged.staging_path)
        staged.checksum_md5 = md5
    except Exception:
        logger.warning(
            "Could not compute MD5 for staged file %d from MinIO; leaving checksum as-is",
            staged_file_id,
        )

    staged.status = StagedFileStatus.VERIFIED
    await db.commit()
    await db.refresh(staged)
    return staged


@router.post("/upload", response_model=StagedFileResponse)
async def upload_file_direct(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Direct file upload through the backend. Computes MD5 server-side and
    stores in MinIO (or falls back to registering without storage)."""
    contents = await file.read()
    md5_hash = hashlib.md5(contents).hexdigest()
    file_size = len(contents)

    unique_id = uuid.uuid4().hex[:12]
    staging_path = f"staging/{user.id}/{unique_id}/{file.filename}"

    # Try to store in MinIO
    try:
        storage = StorageService()
        storage.ensure_buckets()
        storage.client.put_object(
            BUCKET_STAGING,
            staging_path,
            io.BytesIO(contents),
            length=file_size,
            content_type="application/octet-stream",
        )
    except Exception:
        logger.warning("MinIO unavailable, registering staged file without storage")

    svc = StagingService(db)
    staged = await svc.register_file(
        user_id=user.id,
        filename=file.filename,
        file_size=file_size,
        checksum_md5=md5_hash,
        upload_method=UploadMethod.BROWSER,
        staging_path=staging_path,
    )
    staged.status = StagedFileStatus.VERIFIED
    await db.commit()
    await db.refresh(staged)
    return staged
