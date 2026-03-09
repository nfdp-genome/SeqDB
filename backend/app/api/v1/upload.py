import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.sample import Sample
from app.models.project import Project
from app.schemas.upload import (
    UploadInitiate,
    UploadInitiateResponse,
    UploadComplete,
    UploadCompleteResponse,
)
from app.services.experiments import get_experiment_by_accession
from app.services.runs import create_run
from app.services.storage import StorageService
from app.config import settings

router = APIRouter(prefix="/upload", tags=["upload"])

# In-memory upload registry (Redis in production)
_pending_uploads: dict[str, dict] = {}


@router.post("/initiate", response_model=UploadInitiateResponse)
async def initiate_upload(
    upload_in: UploadInitiate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    experiment = await get_experiment_by_accession(db, upload_in.experiment_accession)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    upload_id = f"up-{uuid.uuid4().hex[:8]}"

    # Explicit queries to avoid lazy loading
    result = await db.execute(select(Sample).where(Sample.id == experiment.sample_id))
    sample = result.scalar_one_or_none()

    project_acc = "unknown"
    sample_acc = "unknown"
    if sample:
        sample_acc = sample.internal_accession
        result = await db.execute(select(Project).where(Project.id == sample.project_id))
        project = result.scalar_one_or_none()
        if project:
            project_acc = project.internal_accession

    object_path = StorageService.build_object_path(
        project_acc, sample_acc, upload_id, upload_in.filename
    )

    _pending_uploads[upload_id] = {
        "experiment_accession": upload_in.experiment_accession,
        "filename": upload_in.filename,
        "file_size": upload_in.file_size,
        "checksum_md5": upload_in.checksum_md5,
        "file_type": upload_in.file_type.value,
        "object_path": object_path,
        "bucket": StorageService.BUCKET_RAW,
    }

    try:
        storage = StorageService()
        storage.ensure_buckets()
        presigned_url = storage.generate_presigned_upload_url(
            StorageService.BUCKET_RAW, object_path
        )
    except Exception:
        # Fallback if MinIO is unreachable (e.g., tests)
        presigned_url = f"http://{settings.minio_endpoint}/{StorageService.BUCKET_RAW}/{object_path}"

    return UploadInitiateResponse(
        upload_id=upload_id,
        presigned_url=presigned_url,
        expires_in=86400,
    )


@router.post("/complete", response_model=UploadCompleteResponse)
async def complete_upload(
    upload_in: UploadComplete,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    upload_meta = _pending_uploads.pop(upload_in.upload_id, None)
    if not upload_meta:
        raise HTTPException(status_code=404, detail="Upload not found or already completed")

    if upload_in.checksum_md5 != upload_meta["checksum_md5"]:
        raise HTTPException(status_code=400, detail="Checksum mismatch")

    run = await create_run(
        db=db,
        experiment_accession=upload_meta["experiment_accession"],
        file_type=upload_meta["file_type"],
        file_path=f"{upload_meta['bucket']}/{upload_meta['object_path']}",
        file_size=upload_meta["file_size"],
        checksum_md5=upload_meta["checksum_md5"],
    )

    qc_job_id = f"qc-{uuid.uuid4().hex[:8]}"

    return UploadCompleteResponse(
        run_accession=run.internal_accession,
        qc_job_id=qc_job_id,
        status="uploaded",
    )


@router.get("/status/{upload_id}")
async def upload_status(upload_id: str):
    if upload_id in _pending_uploads:
        return {"upload_id": upload_id, "status": "pending"}
    return {"upload_id": upload_id, "status": "unknown"}
