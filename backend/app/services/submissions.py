from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.submission import Submission
from app.models.project import Project
from app.models.sample import Sample
from app.models.enums import SubmissionStatus
from app.models.user import User
from app.schemas.submission import SubmissionCreate
from app.services.accession import generate_accession, AccessionType
from app.services.validation import validate_sample_metadata


async def create_submission(
    db: AsyncSession, sub_in: SubmissionCreate, user: User
) -> Submission:
    project_result = await db.execute(
        select(Project).where(Project.internal_accession == sub_in.project_accession)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise ValueError(f"Project {sub_in.project_accession} not found")

    result = await db.execute(select(func.count()).select_from(Submission))
    count = result.scalar() + 1

    submission = Submission(
        internal_accession=generate_accession(AccessionType.SUBMISSION, count),
        title=sub_in.title,
        project_id=project.id,
        created_by_id=user.id,
        run_accessions=sub_in.run_accessions,
        status=SubmissionStatus.DRAFT,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


async def validate_submission(db: AsyncSession, accession: str) -> dict:
    result = await db.execute(
        select(Submission).where(Submission.internal_accession == accession)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise ValueError(f"Submission {accession} not found")

    # Get project
    project = await db.get(Project, submission.project_id)

    # Get all samples for project
    samples_result = await db.execute(
        select(Sample).where(Sample.project_id == project.id)
    )
    samples = list(samples_result.scalars().all())

    all_errors = []
    all_warnings = []

    for sample in samples:
        metadata = {
            "organism": sample.organism,
            "tax_id": sample.tax_id,
            "collection_date": str(sample.collection_date),
            "geographic_location": sample.geographic_location,
        }
        if sample.host:
            metadata["host"] = sample.host
        if sample.breed:
            metadata["breed"] = sample.breed
        if sample.sex:
            metadata["sex"] = sample.sex

        errors = validate_sample_metadata(sample.checklist_id, metadata)
        for e in errors:
            all_errors.append({
                "sample": sample.internal_accession,
                "field": e["field"],
                "message": e["message"],
            })

        # Warnings for optional but recommended fields
        if not sample.developmental_stage:
            all_warnings.append(
                f"Sample {sample.internal_accession}: developmental_stage is empty"
            )

    new_status = SubmissionStatus.VALIDATED if not all_errors else SubmissionStatus.FAILED
    submission.status = new_status
    submission.validation_report = {
        "errors": all_errors,
        "warnings": all_warnings,
    }
    await db.commit()

    return {
        "status": new_status.value,
        "errors": all_errors,
        "warnings": all_warnings,
    }


async def get_submission_by_accession(db: AsyncSession, accession: str) -> Submission | None:
    result = await db.execute(
        select(Submission).where(Submission.internal_accession == accession)
    )
    return result.scalar_one_or_none()
