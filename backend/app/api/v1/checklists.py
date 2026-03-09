from fastapi import APIRouter, HTTPException

from app.services.validation import list_checklists, load_checklist

router = APIRouter(prefix="/checklists", tags=["checklists"])


@router.get("/")
async def list_all():
    return list_checklists()


@router.get("/{checklist_id}/schema")
async def get_schema(checklist_id: str):
    schema = load_checklist(checklist_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return schema
