"""NCBI submission API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.config import settings
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.sample import Sample
from app.models.experiment import Experiment
from app.models.run import Run
from app.models.archive_submission import ArchiveSubmission
from app.models.enums import Archive, ArchiveSubmissionStatus
from app.services.archive_tracking import ArchiveTrackingService
from app.ncbi.xml_builder import (
    build_bioproject_xml,
    build_biosample_xml,
    build_sra_xml,
)
from app.ncbi.client import NCBIClient

router = APIRouter(prefix="/ncbi", tags=["NCBI"])


@router.post("/submit/{project_accession}")
async def submit_to_ncbi(
    project_accession: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Submit a project and its entities to NCBI."""
    if not settings.ncbi_api_key:
        raise HTTPException(
            status_code=400,
            detail="NCBI submission is not configured. Set NCBI_API_KEY environment variable.",
        )

    # Load project
    result = await db.execute(
        select(Project).where(Project.internal_accession == project_accession)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Load samples
    result = await db.execute(
        select(Sample).where(Sample.project_id == project.id)
    )
    samples = list(result.scalars().all())
    if not samples:
        raise HTTPException(status_code=400, detail="Project has no samples")

    # Load experiments and runs
    sample_ids = [s.id for s in samples]
    result = await db.execute(
        select(Experiment).where(Experiment.sample_id.in_(sample_ids))
    )
    experiments = list(result.scalars().all())

    exp_ids = [e.id for e in experiments]
    runs = []
    if exp_ids:
        result = await db.execute(
            select(Run).where(Run.experiment_id.in_(exp_ids))
        )
        runs = list(result.scalars().all())

    # Build dicts for XML
    project_dict = {
        "title": project.title,
        "description": project.description,
        "project_type": project.project_type.value,
        "internal_accession": project.internal_accession,
    }

    domain_id = None
    sample_dicts = []
    for s in samples:
        domain_id = s.domain_schema_id or "livestock"
        sample_dicts.append({
            "internal_accession": s.internal_accession,
            "organism": s.organism,
            "tax_id": s.tax_id,
            "breed": s.breed,
            "collection_date": str(s.collection_date) if s.collection_date else None,
            "geographic_location": s.geographic_location,
            "sex": s.sex,
            "host": s.host,
            "tissue": s.tissue,
        })

    exp_dicts = []
    for e in experiments:
        sample = next((s for s in samples if s.id == e.sample_id), None)
        exp_dicts.append({
            "internal_accession": e.internal_accession,
            "platform": e.platform.value,
            "instrument_model": e.instrument_model,
            "library_strategy": e.library_strategy.value,
            "library_source": e.library_source.value,
            "library_layout": e.library_layout.value,
            "sample_accession": sample.internal_accession if sample else "",
        })

    run_dicts = []
    for r in runs:
        exp = next((e for e in experiments if e.id == r.experiment_id), None)
        run_dicts.append({
            "internal_accession": r.internal_accession,
            "filename": r.file_path.split("/")[-1] if r.file_path else "",
            "file_type": r.file_type.value.lower(),
            "checksum_md5": r.checksum_md5,
            "experiment_accession": exp.internal_accession if exp else "",
        })

    # Submit to NCBI
    ncbi_client = NCBIClient(
        base_url=settings.ncbi_submission_url,
        api_key=settings.ncbi_api_key,
    )
    tracking = ArchiveTrackingService(db)
    submissions = []

    # 1. BioProject
    bp_xml = build_bioproject_xml(project_dict, center_name=settings.ncbi_center_name)
    bp_result = await ncbi_client.submit(bp_xml, "BioProject")
    bp_sub = await tracking.create("project", project.internal_accession, Archive.NCBI)
    if bp_result.get("submission_id"):
        await tracking.update_status(
            bp_sub.id, ArchiveSubmissionStatus.SUBMITTED,
            response_data=bp_result,
        )
    submissions.append({"type": "BioProject", "result": bp_result})

    # 2. BioSamples
    if sample_dicts:
        bs_xml = build_biosample_xml(
            sample_dicts, domain_id or "livestock",
            center_name=settings.ncbi_center_name,
        )
        bs_result = await ncbi_client.submit(bs_xml, "BioSample")
        for s in samples:
            sub = await tracking.create("sample", s.internal_accession, Archive.NCBI)
            if bs_result.get("submission_id"):
                await tracking.update_status(
                    sub.id, ArchiveSubmissionStatus.SUBMITTED,
                    response_data=bs_result,
                )
        submissions.append({"type": "BioSample", "result": bs_result})

    # 3. SRA
    if exp_dicts and run_dicts:
        sra_xml = build_sra_xml(
            exp_dicts, run_dicts,
            center_name=settings.ncbi_center_name,
        )
        sra_result = await ncbi_client.submit(sra_xml, "SRA")
        for e in experiments:
            sub = await tracking.create("experiment", e.internal_accession, Archive.NCBI)
            if sra_result.get("submission_id"):
                await tracking.update_status(
                    sub.id, ArchiveSubmissionStatus.SUBMITTED,
                    response_data=sra_result,
                )
        for r in runs:
            sub = await tracking.create("run", r.internal_accession, Archive.NCBI)
            if sra_result.get("submission_id"):
                await tracking.update_status(
                    sub.id, ArchiveSubmissionStatus.SUBMITTED,
                    response_data=sra_result,
                )
        submissions.append({"type": "SRA", "result": sra_result})

    return {
        "project_accession": project_accession,
        "submissions": submissions,
    }


@router.get("/status/{project_accession}")
async def get_ncbi_status(
    project_accession: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get NCBI submission status for all entities in a project."""
    result = await db.execute(
        select(Project).where(Project.internal_accession == project_accession)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tracking = ArchiveTrackingService(db)
    project_subs = await tracking.list_for_entity("project", project_accession)

    # Get sample accessions
    result = await db.execute(
        select(Sample.internal_accession).where(Sample.project_id == project.id)
    )
    sample_accs = [row[0] for row in result.all()]

    all_subs = list(project_subs)
    for acc in sample_accs:
        subs = await tracking.list_for_entity("sample", acc)
        all_subs.extend(subs)

    return {
        "project_accession": project_accession,
        "submissions": [
            {
                "id": s.id,
                "entity_type": s.entity_type,
                "entity_accession": s.entity_accession,
                "archive": s.archive.value,
                "archive_accession": s.archive_accession,
                "status": s.status.value,
                "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
            }
            for s in all_subs
        ],
    }


@router.post("/retry/{submission_id}")
async def retry_ncbi_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retry a failed NCBI submission."""
    result = await db.execute(
        select(ArchiveSubmission).where(ArchiveSubmission.id == submission_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    if sub.status != ArchiveSubmissionStatus.FAILED:
        raise HTTPException(status_code=400, detail="Only failed submissions can be retried")

    tracking = ArchiveTrackingService(db)
    await tracking.update_status(sub.id, ArchiveSubmissionStatus.DRAFT)
    return {"id": sub.id, "status": "draft", "message": "Submission reset to draft for retry"}
