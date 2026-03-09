from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.schemas.experiment import ExperimentCreate, ExperimentResponse
from app.services.experiments import create_experiment, get_experiment_by_accession, list_experiments

router = APIRouter(prefix="/experiments", tags=["experiments"])


def _exp_to_response(exp) -> ExperimentResponse:
    return ExperimentResponse(
        accession=exp.internal_accession,
        ena_accession=exp.ena_accession,
        platform=exp.platform,
        instrument_model=exp.instrument_model,
        library_strategy=exp.library_strategy,
        library_source=exp.library_source,
        library_layout=exp.library_layout,
        insert_size=exp.insert_size,
        created_at=exp.created_at,
    )


@router.post("/", response_model=ExperimentResponse, status_code=201)
async def create(
    exp_in: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        experiment = await create_experiment(db, exp_in)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _exp_to_response(experiment)


@router.get("/", response_model=list[ExperimentResponse])
async def list_all(page: int = 1, per_page: int = 20, db: AsyncSession = Depends(get_db)):
    experiments = await list_experiments(db, page, per_page)
    return [_exp_to_response(e) for e in experiments]


@router.get("/{accession}", response_model=ExperimentResponse)
async def get(accession: str, db: AsyncSession = Depends(get_db)):
    experiment = await get_experiment_by_accession(db, accession)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return _exp_to_response(experiment)
