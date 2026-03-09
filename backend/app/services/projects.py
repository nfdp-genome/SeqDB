from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.accession import generate_accession, AccessionType


async def create_project(db: AsyncSession, project_in: ProjectCreate, user: User) -> Project:
    result = await db.execute(select(func.count()).select_from(Project))
    count = result.scalar() + 1
    project = Project(
        internal_accession=generate_accession(AccessionType.PROJECT, count),
        title=project_in.title,
        description=project_in.description,
        project_type=project_in.project_type,
        release_date=project_in.release_date,
        license=project_in.license,
        created_by_id=user.id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def update_project(db: AsyncSession, project: Project, project_in: ProjectUpdate) -> Project:
    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    return project


async def get_project_by_accession(db: AsyncSession, accession: str) -> Project | None:
    result = await db.execute(select(Project).where(Project.internal_accession == accession))
    return result.scalar_one_or_none()


async def list_projects(db: AsyncSession, page: int = 1, per_page: int = 20) -> list[Project]:
    offset = (page - 1) * per_page
    result = await db.execute(
        select(Project).offset(offset).limit(per_page).order_by(Project.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_project(db: AsyncSession, accession: str, user_id: int) -> bool:
    """Delete a project by accession if the user owns it and it has no samples."""
    result = await db.execute(
        select(Project).where(Project.internal_accession == accession)
    )
    project = result.scalar_one_or_none()
    if not project:
        return False
    if project.created_by_id != user_id:
        return False
    # Check for linked samples
    from app.models.sample import Sample
    sample_count = await db.execute(
        select(func.count()).select_from(Sample).where(Sample.project_id == project.id)
    )
    if sample_count.scalar() > 0:
        return False
    await db.delete(project)
    await db.commit()
    return True
