from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.database import get_db
from app.models.project import Project
from app.models.sample import Sample

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/")
async def search(
    q: str = Query(..., min_length=1),
    type: str = Query("project,sample"),
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
):
    types = [t.strip() for t in type.split(",")]
    results = []
    offset = (page - 1) * per_page

    if "project" in types:
        query = select(Project).where(
            or_(
                Project.title.ilike(f"%{q}%"),
                Project.description.ilike(f"%{q}%"),
            )
        ).offset(offset).limit(per_page)
        result = await db.execute(query)
        for s in result.scalars().all():
            results.append({
                "type": "project",
                "accession": s.internal_accession,
                "title": s.title,
                "description": s.description,
            })

    if "sample" in types:
        query = select(Sample).where(
            or_(
                Sample.organism.ilike(f"%{q}%"),
                Sample.breed.ilike(f"%{q}%"),
                Sample.geographic_location.ilike(f"%{q}%"),
            )
        ).offset(offset).limit(per_page)
        result = await db.execute(query)
        for s in result.scalars().all():
            results.append({
                "type": "sample",
                "accession": s.internal_accession,
                "organism": s.organism,
                "breed": s.breed,
                "geographic_location": s.geographic_location,
            })

    return {"query": q, "total": len(results), "results": results}
