"""Background job to poll NCBI for submission status updates."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.archive_submission import ArchiveSubmission
from app.models.enums import Archive, ArchiveSubmissionStatus
from app.models.project import Project
from app.models.sample import Sample
from app.models.experiment import Experiment
from app.models.run import Run
from app.ncbi.client import NCBIClient
from app.config import settings


async def poll_ncbi_submissions(db: AsyncSession) -> dict:
    """Poll NCBI for status updates on pending submissions.

    Intended to be called by an ARQ background worker.
    Returns summary of updates made.
    """
    if not settings.ncbi_api_key:
        return {"skipped": True, "reason": "NCBI not configured"}

    # Find all SUBMITTED archive submissions for NCBI
    result = await db.execute(
        select(ArchiveSubmission).where(
            ArchiveSubmission.archive == Archive.NCBI,
            ArchiveSubmission.status == ArchiveSubmissionStatus.SUBMITTED,
        )
    )
    pending = list(result.scalars().all())

    if not pending:
        return {"checked": 0, "updated": 0}

    client = NCBIClient(
        base_url=settings.ncbi_submission_url,
        api_key=settings.ncbi_api_key,
    )

    # Group by submission_id from response_data
    submission_ids = set()
    for sub in pending:
        if sub.response_data and sub.response_data.get("submission_id"):
            submission_ids.add(sub.response_data["submission_id"])

    updated = 0
    for ncbi_sub_id in submission_ids:
        status_resp = await client.check_status(ncbi_sub_id)

        if status_resp.get("status") == "error":
            continue

        ncbi_status = status_resp.get("status", "")

        if ncbi_status == "processed-ok":
            # Extract accessions from response
            accessions = {}
            for action in status_resp.get("actions", []):
                for resp in action.get("responses", []):
                    if resp.get("accession"):
                        spuid = resp.get("object_id", "")
                        accessions[spuid] = resp["accession"]

            # Update matching submissions
            for sub in pending:
                if (sub.response_data and
                        sub.response_data.get("submission_id") == ncbi_sub_id):
                    ncbi_acc = accessions.get(sub.entity_accession)
                    sub.status = ArchiveSubmissionStatus.PUBLIC
                    if ncbi_acc:
                        sub.archive_accession = ncbi_acc
                        await _update_entity_accession(
                            db, sub.entity_type, sub.entity_accession, ncbi_acc
                        )
                    sub.response_data = status_resp
                    updated += 1

        elif ncbi_status in ("failed", "processing-error"):
            for sub in pending:
                if (sub.response_data and
                        sub.response_data.get("submission_id") == ncbi_sub_id):
                    sub.status = ArchiveSubmissionStatus.FAILED
                    sub.response_data = status_resp
                    updated += 1

    await db.commit()
    return {"checked": len(submission_ids), "updated": updated}


async def _update_entity_accession(
    db: AsyncSession,
    entity_type: str,
    entity_accession: str,
    ncbi_accession: str,
) -> None:
    """Update the ncbi_accession field on the entity model."""
    model_map = {
        "project": Project,
        "sample": Sample,
        "experiment": Experiment,
        "run": Run,
    }
    model = model_map.get(entity_type)
    if not model:
        return

    result = await db.execute(
        select(model).where(model.internal_accession == entity_accession)
    )
    entity = result.scalar_one_or_none()
    if entity:
        entity.ncbi_accession = ncbi_accession
