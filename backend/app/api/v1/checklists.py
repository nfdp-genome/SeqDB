from fastapi import APIRouter, HTTPException

from app.services.validation import list_checklists, load_checklist
from app.schemas.domains import list_domains

router = APIRouter(prefix="/checklists", tags=["checklists"])


@router.get("/")
async def list_all():
    return list_checklists()


@router.get("/domains")
async def list_domain_schemas():
    """List available domain schemas for NCBI/ENA mapping."""
    return list_domains()


@router.get("/{checklist_id}/schema")
async def get_schema(checklist_id: str):
    schema = load_checklist(checklist_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return schema
