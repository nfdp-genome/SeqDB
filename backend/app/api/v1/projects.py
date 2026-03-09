from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.models.sample import Sample
from app.services.projects import create_project, get_project_by_accession, list_projects, delete_project, update_project

router = APIRouter(prefix="/projects", tags=["projects"])


def _project_to_response(project) -> ProjectResponse:
    return ProjectResponse(
        accession=project.internal_accession,
        ena_accession=project.ena_accession,
        title=project.title,
        description=project.description,
        project_type=project.project_type,
        release_date=project.release_date,
        license=project.license,
        created_at=project.created_at,
    )


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = await create_project(db, project_in, user)
    return _project_to_response(project)


@router.get("/", response_model=list[ProjectResponse])
async def list_all(page: int = 1, per_page: int = 20, db: AsyncSession = Depends(get_db)):
    projects = await list_projects(db, page, per_page)
    return [_project_to_response(p) for p in projects]


@router.get("/{accession}", response_model=ProjectResponse)
async def get(accession: str, db: AsyncSession = Depends(get_db)):
    project = await get_project_by_accession(db, accession)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_to_response(project)


@router.put("/{accession}", response_model=ProjectResponse)
async def update(
    accession: str,
    project_in: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = await get_project_by_accession(db, accession)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.created_by_id != user.id:
        raise HTTPException(status_code=403, detail="Not the project owner")
    project = await update_project(db, project, project_in)
    return _project_to_response(project)


@router.get("/{accession}/fair")
async def fair_score(accession: str, db: AsyncSession = Depends(get_db)):
    """Per-project FAIR score with actionable breakdown."""
    from sqlalchemy import select, func
    from app.models.experiment import Experiment
    from app.models.run import Run

    project = await get_project_by_accession(db, accession)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Fetch samples for this project
    result = await db.execute(select(Sample).where(Sample.project_id == project.id))
    samples = list(result.scalars().all())
    total_samples = len(samples)

    # Count experiments and runs
    sample_ids = [s.id for s in samples]
    exp_count = 0
    run_count = 0
    if sample_ids:
        r = await db.execute(
            select(func.count()).select_from(Experiment).where(Experiment.sample_id.in_(sample_ids))
        )
        exp_count = r.scalar()
        r = await db.execute(
            select(func.count()).select_from(Run)
            .join(Experiment)
            .where(Experiment.sample_id.in_(sample_ids))
        )
        run_count = r.scalar()

    # --- Findable ---
    f_checks = {
        "has_accession": bool(project.internal_accession),
        "has_title": bool(project.title and len(project.title) > 3),
        "has_description": bool(project.description and len(project.description) > 10),
        "has_samples": total_samples > 0,
    }
    findable = round(sum(f_checks.values()) / len(f_checks) * 100)

    # --- Accessible ---
    a_checks = {
        "has_license": bool(project.license),
        "has_release_date": project.release_date is not None,
        "samples_have_accessions": total_samples > 0 and all(s.internal_accession for s in samples),
    }
    accessible = round(sum(a_checks.values()) / len(a_checks) * 100)

    # --- Interoperable ---
    samples_with_checklist = sum(1 for s in samples if s.checklist_id)
    samples_with_taxid = sum(1 for s in samples if s.tax_id)
    i_checks = {
        "all_samples_have_checklist": total_samples > 0 and samples_with_checklist == total_samples,
        "all_samples_have_taxid": total_samples > 0 and samples_with_taxid == total_samples,
        "has_experiments": exp_count > 0,
    }
    interoperable = round(sum(i_checks.values()) / len(i_checks) * 100)

    # --- Reusable ---
    samples_with_organism = sum(1 for s in samples if s.organism)
    samples_with_location = sum(1 for s in samples if s.geographic_location)
    samples_with_date = sum(1 for s in samples if s.collection_date)
    r_checks = {
        "has_license": bool(project.license),
        "all_samples_have_organism": total_samples > 0 and samples_with_organism == total_samples,
        "all_samples_have_location": total_samples > 0 and samples_with_location == total_samples,
        "all_samples_have_date": total_samples > 0 and samples_with_date == total_samples,
        "has_data_files": run_count > 0,
    }
    reusable = round(sum(r_checks.values()) / len(r_checks) * 100)

    # Build suggestions
    suggestions = []
    if not f_checks["has_description"]:
        suggestions.append("Add a meaningful description (>10 characters)")
    if not f_checks["has_samples"]:
        suggestions.append("Add at least one sample to the project")
    if not a_checks["has_release_date"]:
        suggestions.append("Set a release date for the project")
    if not a_checks["has_license"]:
        suggestions.append("Assign a license (e.g. CC-BY)")
    if total_samples > 0 and not i_checks["all_samples_have_checklist"]:
        suggestions.append(f"{total_samples - samples_with_checklist} sample(s) missing checklist")
    if not i_checks["has_experiments"]:
        suggestions.append("Link experiments to your samples")
    if not r_checks["has_data_files"]:
        suggestions.append("Upload data files (FASTQ, BAM, VCF)")
    if total_samples > 0 and not r_checks["all_samples_have_location"]:
        suggestions.append(f"{total_samples - samples_with_location} sample(s) missing geographic location")

    return {
        "accession": project.internal_accession,
        "scores": {
            "findable": findable,
            "accessible": accessible,
            "interoperable": interoperable,
            "reusable": reusable,
        },
        "checks": {
            "findable": f_checks,
            "accessible": a_checks,
            "interoperable": i_checks,
            "reusable": r_checks,
        },
        "suggestions": suggestions,
        "counts": {
            "samples": total_samples,
            "experiments": exp_count,
            "runs": run_count,
        },
    }


@router.delete("/{accession}", status_code=200)
async def delete(
    accession: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a project. Only the creator can delete, and only if it has no linked samples."""
    deleted = await delete_project(db, accession, user.id)
    if not deleted:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete: project not found, not owned by you, or has linked samples",
        )
    return {"detail": "Project deleted"}
