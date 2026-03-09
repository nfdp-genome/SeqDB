"""Run endpoints: list, get, download, QC reports."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.run import RunResponse
from app.services.runs import get_run_by_accession, list_runs, get_qc_reports
from app.services.storage import StorageService

log = logging.getLogger(__name__)

router = APIRouter(prefix="/runs", tags=["runs"])


def _run_to_response(run) -> RunResponse:
    return RunResponse(
        accession=run.internal_accession,
        ena_accession=run.ena_accession,
        file_type=run.file_type,
        file_size=run.file_size,
        checksum_md5=run.checksum_md5,
        created_at=run.created_at,
    )


@router.get("/", response_model=list[RunResponse])
async def list_all(page: int = 1, per_page: int = 20, db: AsyncSession = Depends(get_db)):
    runs = await list_runs(db, page, per_page)
    return [_run_to_response(r) for r in runs]


@router.get("/{accession}", response_model=RunResponse)
async def get(accession: str, db: AsyncSession = Depends(get_db)):
    run = await get_run_by_accession(db, accession)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return _run_to_response(run)


@router.get("/{accession}/download")
async def download(accession: str, db: AsyncSession = Depends(get_db)):
    """Generate a presigned download URL for the run's file (ENA-like)."""
    run = await get_run_by_accession(db, accession)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    file_path = run.file_path
    if not file_path:
        raise HTTPException(status_code=404, detail="No file associated with this run")

    # file_path format: "bucket/object/path" or just "filename"
    # Try to parse bucket from path, fall back to raw bucket
    parts = file_path.split("/", 1)
    if len(parts) == 2 and parts[0].startswith("nfdp-"):
        bucket, object_path = parts[0], parts[1]
    else:
        bucket = StorageService.BUCKET_RAW
        object_path = file_path

    try:
        storage = StorageService()
        url = storage.generate_presigned_download_url(bucket, object_path, expires_hours=24)
        return RedirectResponse(url=url, status_code=307)
    except Exception as e:
        log.warning("Presigned URL generation failed for %s: %s", accession, e)
        # In dev mode without MinIO, return metadata instead
        return {
            "accession": accession,
            "file_path": file_path,
            "file_size": run.file_size,
            "checksum_md5": run.checksum_md5,
            "message": "Direct download unavailable — file stored at the path above",
        }


@router.get("/{accession}/qc")
async def get_qc(accession: str, db: AsyncSession = Depends(get_db)):
    run = await get_run_by_accession(db, accession)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    reports = await get_qc_reports(db, accession)
    if not reports:
        return {"status": "pending", "reports": []}
    return {
        "status": reports[0].status.value,
        "tool": reports[0].tool,
        "summary": reports[0].summary,
        "report_url": reports[0].report_path,
        "reports": [
            {
                "tool": r.tool,
                "status": r.status.value,
                "summary": r.summary,
            }
            for r in reports
        ],
    }
