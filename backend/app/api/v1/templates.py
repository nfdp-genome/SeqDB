from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.templates import generate_template_tsv, parse_template_tsv
from app.services.validation import validate_sample_metadata, load_checklist
from app.services.samples import create_samples_bulk

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/{checklist_id}/download")
async def download_template(checklist_id: str):
    """Download a TSV template for a given checklist."""
    tsv = generate_template_tsv(checklist_id)
    if tsv is None:
        raise HTTPException(status_code=404, detail=f"Checklist '{checklist_id}' not found")

    return StreamingResponse(
        io.BytesIO(tsv.encode("utf-8")),
        media_type="text/tab-separated-values",
        headers={
            "Content-Disposition": f'attachment; filename="{checklist_id}_template.tsv"'
        },
    )


@router.post("/upload")
async def upload_template(
    file: UploadFile = File(...),
    project_accession: str = Form(...),
    checklist_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Upload a filled TSV template, validate, and create samples."""
    content = (await file.read()).decode("utf-8")
    headers, rows = parse_template_tsv(content)

    if not rows:
        raise HTTPException(status_code=400, detail="Template is empty — no data rows found")

    schema = load_checklist(checklist_id)
    if schema is None:
        raise HTTPException(status_code=404, detail=f"Checklist '{checklist_id}' not found")

    # Validate each row against checklist
    validation_errors = []
    for i, row in enumerate(rows, start=2):
        # Convert tax_id to int for validation
        metadata = dict(row)
        if "tax_id" in metadata and metadata["tax_id"]:
            try:
                metadata["tax_id"] = int(metadata["tax_id"])
            except ValueError:
                pass
        errors = validate_sample_metadata(checklist_id, metadata)
        for err in errors:
            validation_errors.append({"row": i, **err})

    if validation_errors:
        return {
            "status": "validation_failed",
            "valid_rows": len(rows) - len({e["row"] for e in validation_errors}),
            "error_rows": len({e["row"] for e in validation_errors}),
            "errors": validation_errors,
        }

    # All rows valid — create samples using bulk service
    result = await create_samples_bulk(db, content, project_accession, checklist_id)

    return {
        "status": "created",
        "created": result["created"],
        "errors": result["errors"],
        "error_details": result["error_details"],
    }
