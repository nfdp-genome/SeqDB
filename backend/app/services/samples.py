import csv
import io
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.sample import Sample
from app.models.project import Project
from app.schemas.sample import SampleCreate
from app.services.accession import generate_accession, AccessionType


async def get_project_by_accession(db: AsyncSession, accession: str) -> Project | None:
    result = await db.execute(select(Project).where(Project.internal_accession == accession))
    return result.scalar_one_or_none()


async def create_sample(db: AsyncSession, sample_in: SampleCreate) -> Sample:
    project = await get_project_by_accession(db, sample_in.project_accession)
    if not project:
        raise ValueError(f"Project {sample_in.project_accession} not found")

    result = await db.execute(select(func.count()).select_from(Sample))
    count = result.scalar() + 1

    sample = Sample(
        internal_accession=generate_accession(AccessionType.SAMPLE, count),
        organism=sample_in.organism,
        tax_id=sample_in.tax_id,
        breed=sample_in.breed,
        collection_date=sample_in.collection_date,
        geographic_location=sample_in.geographic_location,
        host=sample_in.host,
        tissue=sample_in.tissue,
        developmental_stage=sample_in.developmental_stage,
        sex=sample_in.sex,
        checklist_id=sample_in.checklist_id,
        custom_fields=sample_in.custom_fields,
        project_id=project.id,
    )
    db.add(sample)
    await db.commit()
    await db.refresh(sample)
    return sample


async def create_samples_bulk(
    db: AsyncSession, tsv_content: str, project_accession: str, checklist_id: str
) -> dict:
    project = await get_project_by_accession(db, project_accession)
    if not project:
        raise ValueError(f"Project {project_accession} not found")

    reader = csv.DictReader(io.StringIO(tsv_content), delimiter="\t")
    created = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):
        try:
            result = await db.execute(select(func.count()).select_from(Sample))
            count = result.scalar() + 1

            sample = Sample(
                internal_accession=generate_accession(AccessionType.SAMPLE, count),
                organism=row["organism"],
                tax_id=int(row["tax_id"]),
                breed=row.get("breed"),
                collection_date=date.fromisoformat(row["collection_date"]),
                geographic_location=row["geographic_location"],
                host=row.get("host"),
                tissue=row.get("tissue"),
                sex=row.get("sex"),
                checklist_id=checklist_id,
                project_id=project.id,
            )
            db.add(sample)
            await db.flush()
            created += 1
        except Exception as e:
            errors.append({"row": row_num, "field": "unknown", "message": str(e)})

    await db.commit()
    return {"created": created, "errors": len(errors), "error_details": errors}


async def get_sample_by_accession(db: AsyncSession, accession: str) -> Sample | None:
    result = await db.execute(select(Sample).where(Sample.internal_accession == accession))
    return result.scalar_one_or_none()


async def list_samples(
    db: AsyncSession, project_accession: str | None = None, page: int = 1, per_page: int = 20
) -> list[Sample]:
    query = select(Sample)
    if project_accession:
        project = await get_project_by_accession(db, project_accession)
        if project:
            query = query.where(Sample.project_id == project.id)
    offset = (page - 1) * per_page
    result = await db.execute(query.offset(offset).limit(per_page).order_by(Sample.created_at.desc()))
    return list(result.scalars().all())
