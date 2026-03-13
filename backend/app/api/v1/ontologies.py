from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.v1.deps import get_current_user
from app.models.enums import OntologyType
from app.models.user import User
from app.schemas.ontology import OntologyTermResponse
from app.services.ontology_service import OntologyService

router = APIRouter(prefix="/ontologies", tags=["Ontologies"])


@router.get("/search", response_model=list[OntologyTermResponse])
async def search_ontology_terms(
    q: str = Query(..., min_length=1, description="Search query"),
    ontology: OntologyType = Query(..., description="Ontology to search"),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = OntologyService(db)
    results = await service.search_terms(q, ontology, limit)
    return results


@router.post("/seed")
async def seed_ontologies(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = OntologyService(db)
    counts = await service.seed_all()
    return counts
