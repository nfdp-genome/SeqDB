from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.schemas.sample import SampleCreate, SampleResponse
from app.services.samples import create_sample, get_sample_by_accession, list_samples, create_samples_bulk

router = APIRouter(prefix="/samples", tags=["samples"])


def _sample_to_response(sample) -> SampleResponse:
    return SampleResponse(
        accession=sample.internal_accession,
        ena_accession=sample.ena_accession,
        organism=sample.organism,
        tax_id=sample.tax_id,
        breed=sample.breed,
        collection_date=sample.collection_date,
        geographic_location=sample.geographic_location,
        checklist_id=sample.checklist_id,
        created_at=sample.created_at,
    )


@router.post("/", response_model=SampleResponse, status_code=201)
async def create(
    sample_in: SampleCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        sample = await create_sample(db, sample_in)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _sample_to_response(sample)


@router.post("/bulk", status_code=201)
async def bulk_create(
    file: UploadFile = File(...),
    project_accession: str = Form(...),
    checklist_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = (await file.read()).decode("utf-8")
    try:
        result = await create_samples_bulk(db, content, project_accession, checklist_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


@router.get("/", response_model=list[SampleResponse])
async def list_all(
    project_accession: str | None = None,
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
):
    samples = await list_samples(db, project_accession, page, per_page)
    return [_sample_to_response(s) for s in samples]


@router.get("/{accession}", response_model=SampleResponse)
async def get(accession: str, db: AsyncSession = Depends(get_db)):
    sample = await get_sample_by_accession(db, accession)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    return _sample_to_response(sample)
