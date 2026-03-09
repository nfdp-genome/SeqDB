from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.experiment import Experiment
from app.models.sample import Sample
from app.schemas.experiment import ExperimentCreate
from app.services.accession import generate_accession, AccessionType


async def get_sample_by_accession(db: AsyncSession, accession: str) -> Sample | None:
    result = await db.execute(select(Sample).where(Sample.internal_accession == accession))
    return result.scalar_one_or_none()


async def create_experiment(db: AsyncSession, exp_in: ExperimentCreate) -> Experiment:
    sample = await get_sample_by_accession(db, exp_in.sample_accession)
    if not sample:
        raise ValueError(f"Sample {exp_in.sample_accession} not found")

    result = await db.execute(select(func.count()).select_from(Experiment))
    count = result.scalar() + 1

    experiment = Experiment(
        internal_accession=generate_accession(AccessionType.EXPERIMENT, count),
        platform=exp_in.platform,
        instrument_model=exp_in.instrument_model,
        library_strategy=exp_in.library_strategy,
        library_source=exp_in.library_source,
        library_layout=exp_in.library_layout,
        insert_size=exp_in.insert_size,
        sample_id=sample.id,
    )
    db.add(experiment)
    await db.commit()
    await db.refresh(experiment)
    return experiment


async def get_experiment_by_accession(db: AsyncSession, accession: str) -> Experiment | None:
    result = await db.execute(
        select(Experiment).where(Experiment.internal_accession == accession)
    )
    return result.scalar_one_or_none()


async def list_experiments(db: AsyncSession, page: int = 1, per_page: int = 20) -> list[Experiment]:
    offset = (page - 1) * per_page
    result = await db.execute(
        select(Experiment).offset(offset).limit(per_page).order_by(Experiment.created_at.desc())
    )
    return list(result.scalars().all())
