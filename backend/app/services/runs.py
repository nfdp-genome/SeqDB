from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.run import Run
from app.models.experiment import Experiment
from app.models.qc_report import QCReport
from app.services.accession import generate_accession, AccessionType


async def get_experiment_by_accession(db: AsyncSession, accession: str) -> Experiment | None:
    result = await db.execute(
        select(Experiment).where(Experiment.internal_accession == accession)
    )
    return result.scalar_one_or_none()


async def create_run(
    db: AsyncSession,
    experiment_accession: str,
    file_type: str,
    file_path: str,
    file_size: int,
    checksum_md5: str,
    checksum_sha256: str | None = None,
) -> Run:
    experiment = await get_experiment_by_accession(db, experiment_accession)
    if not experiment:
        raise ValueError(f"Experiment {experiment_accession} not found")

    result = await db.execute(select(func.count()).select_from(Run))
    count = result.scalar() + 1

    run = Run(
        internal_accession=generate_accession(AccessionType.RUN, count),
        file_type=file_type,
        file_path=file_path,
        file_size=file_size,
        checksum_md5=checksum_md5,
        checksum_sha256=checksum_sha256,
        experiment_id=experiment.id,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


async def get_run_by_accession(db: AsyncSession, accession: str) -> Run | None:
    result = await db.execute(select(Run).where(Run.internal_accession == accession))
    return result.scalar_one_or_none()


async def list_runs(db: AsyncSession, page: int = 1, per_page: int = 20) -> list[Run]:
    offset = (page - 1) * per_page
    result = await db.execute(
        select(Run).offset(offset).limit(per_page).order_by(Run.created_at.desc())
    )
    return list(result.scalars().all())


async def get_qc_reports(db: AsyncSession, run_accession: str) -> list[QCReport]:
    run = await get_run_by_accession(db, run_accession)
    if not run:
        return []
    result = await db.execute(select(QCReport).where(QCReport.run_id == run.id))
    return list(result.scalars().all())
