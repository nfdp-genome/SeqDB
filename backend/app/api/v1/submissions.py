from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.schemas.submission import SubmissionCreate, SubmissionResponse
from app.services.submissions import (
    create_submission,
    validate_submission,
    get_submission_by_accession,
)

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("/", response_model=SubmissionResponse, status_code=201)
async def create(
    sub_in: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        submission = await create_submission(db, sub_in, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return SubmissionResponse(
        submission_id=submission.internal_accession,
        title=submission.title,
        status=submission.status,
        created_at=submission.created_at,
    )


@router.get("/{accession}", response_model=SubmissionResponse)
async def get(accession: str, db: AsyncSession = Depends(get_db)):
    submission = await get_submission_by_accession(db, accession)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return SubmissionResponse(
        submission_id=submission.internal_accession,
        title=submission.title,
        status=submission.status,
        created_at=submission.created_at,
    )


@router.post("/{accession}/validate")
async def validate(
    accession: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        result = await validate_submission(db, accession)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


@router.get("/{accession}/report")
async def get_report(accession: str, db: AsyncSession = Depends(get_db)):
    submission = await get_submission_by_accession(db, accession)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return {
        "submission_id": submission.internal_accession,
        "status": submission.status.value,
        "report": submission.validation_report,
    }
