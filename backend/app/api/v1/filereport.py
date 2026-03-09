"""ENA-style file report API: query files by accession (project, sample, experiment, or run)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.project import Project
from app.models.sample import Sample
from app.models.experiment import Experiment
from app.models.run import Run

router = APIRouter(prefix="/filereport", tags=["filereport"])


def _run_to_file_entry(run: Run, sample: Sample, experiment: Experiment, project_acc: str, base_url: str) -> dict:
    """Build an ENA-style file report entry for a single run."""
    filename = run.file_path.rsplit("/", 1)[-1] if run.file_path else ""
    return {
        "run_accession": run.internal_accession,
        "experiment_accession": experiment.internal_accession,
        "sample_accession": sample.internal_accession,
        "project_accession": project_acc,
        "organism": sample.organism,
        "tax_id": sample.tax_id,
        "file_type": run.file_type.value if hasattr(run.file_type, "value") else str(run.file_type),
        "filename": filename,
        "file_path": run.file_path,
        "file_size": run.file_size,
        "checksum_md5": run.checksum_md5,
        "checksum_sha256": run.checksum_sha256,
        "download_url": f"{base_url}/api/v1/runs/{run.internal_accession}/download",
        "platform": experiment.platform.value if hasattr(experiment.platform, "value") else str(experiment.platform),
        "instrument_model": experiment.instrument_model,
        "library_strategy": experiment.library_strategy.value if hasattr(experiment.library_strategy, "value") else str(experiment.library_strategy),
        "library_layout": experiment.library_layout.value if hasattr(experiment.library_layout, "value") else str(experiment.library_layout),
    }


@router.get("/")
async def filereport(
    accession: str = Query(..., description="Project, sample, experiment, or run accession"),
    result: str = Query("read_run", description="Result type (read_run)"),
    db: AsyncSession = Depends(get_db),
):
    """
    ENA-style file report endpoint.

    Query by any accession type to get file metadata and download URLs.

    Examples:
      GET /filereport?accession=NFDP-PRJ-000001
      GET /filereport?accession=NFDP-SAM-000001
      GET /filereport?accession=NFDP-EXP-000001
      GET /filereport?accession=NFDP-RUN-000001
    """
    # Use a relative base_url — frontend will resolve it
    base_url = ""

    entries = []

    if accession.startswith("NFDP-PRJ-"):
        # Project → all samples → all experiments → all runs
        stmt = (
            select(Project)
            .where(Project.internal_accession == accession)
            .options(
                selectinload(Project.samples)
                .selectinload(Sample.experiments)
                .selectinload(Experiment.runs)
            )
        )
        proj = (await db.execute(stmt)).scalar_one_or_none()
        if not proj:
            raise HTTPException(status_code=404, detail=f"Project '{accession}' not found")
        for sample in proj.samples:
            for exp in sample.experiments:
                for run in exp.runs:
                    entries.append(_run_to_file_entry(run, sample, exp, accession, base_url))

    elif accession.startswith("NFDP-SAM-"):
        stmt = (
            select(Sample)
            .where(Sample.internal_accession == accession)
            .options(
                selectinload(Sample.experiments)
                .selectinload(Experiment.runs)
            )
        )
        sample = (await db.execute(stmt)).scalar_one_or_none()
        if not sample:
            raise HTTPException(status_code=404, detail=f"Sample '{accession}' not found")
        # Get project accession
        proj = await db.get(Project, sample.project_id)
        proj_acc = proj.internal_accession if proj else ""
        for exp in sample.experiments:
            for run in exp.runs:
                entries.append(_run_to_file_entry(run, sample, exp, proj_acc, base_url))

    elif accession.startswith("NFDP-EXP-"):
        stmt = (
            select(Experiment)
            .where(Experiment.internal_accession == accession)
            .options(selectinload(Experiment.runs))
        )
        exp = (await db.execute(stmt)).scalar_one_or_none()
        if not exp:
            raise HTTPException(status_code=404, detail=f"Experiment '{accession}' not found")
        sample = await db.get(Sample, exp.sample_id)
        proj = await db.get(Project, sample.project_id) if sample else None
        proj_acc = proj.internal_accession if proj else ""
        for run in exp.runs:
            entries.append(_run_to_file_entry(run, sample, exp, proj_acc, base_url))

    elif accession.startswith("NFDP-RUN-"):
        run = (await db.execute(
            select(Run).where(Run.internal_accession == accession)
        )).scalar_one_or_none()
        if not run:
            raise HTTPException(status_code=404, detail=f"Run '{accession}' not found")
        exp = await db.get(Experiment, run.experiment_id)
        sample = await db.get(Sample, exp.sample_id) if exp else None
        proj = await db.get(Project, sample.project_id) if sample else None
        proj_acc = proj.internal_accession if proj else ""
        if sample and exp:
            entries.append(_run_to_file_entry(run, sample, exp, proj_acc, base_url))

    else:
        raise HTTPException(status_code=400, detail=f"Unrecognized accession format: '{accession}'")

    return entries
