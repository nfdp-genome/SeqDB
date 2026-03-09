"""Bulk submit API: template download, validation, and submission confirmation."""

import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.templates import generate_template_tsv
from app.services.validation import load_checklist
from app.services.bulk_submit import BulkSubmitService

router = APIRouter(prefix="/bulk-submit", tags=["bulk-submit"])

# Columns added to bulk sample sheet beyond checklist fields
BULK_EXTRA_COLUMNS = [
    "sample_alias",
    "filename_forward",
    "filename_reverse",
    "md5_forward",
    "md5_reverse",
    "library_strategy",
    "platform",
    "instrument_model",
]


def _report_to_dict(report, parsed_rows=None, required_fields=None, all_headers=None) -> dict:
    """Serialize a ValidationReport to a JSON-safe dict with per-cell status."""
    result_rows = []
    for idx, rv in enumerate(report.rows):
        row_dict = {
            "row_num": rv.row_num,
            "sample_alias": rv.sample_alias,
            "errors": rv.errors,
            "warnings": rv.warnings,
            "forward_file": {
                "staged_file_id": rv.forward_file.staged_file_id,
                "filename": rv.forward_file.filename,
                "md5": rv.forward_file.md5,
                "direction": rv.forward_file.direction,
            } if rv.forward_file else None,
            "reverse_file": {
                "staged_file_id": rv.reverse_file.staged_file_id,
                "filename": rv.reverse_file.filename,
                "md5": rv.reverse_file.md5,
                "direction": rv.reverse_file.direction,
            } if rv.reverse_file else None,
        }

        # Add per-cell data and status for the preview table
        if parsed_rows and idx < len(parsed_rows):
            raw = parsed_rows[idx]
            cells = {}
            for col in (all_headers or []):
                val = (raw.get(col, "") or "").strip()
                is_required = col in (required_fields or []) or col == "sample_alias"
                if not val and is_required:
                    status = "missing_required"
                elif not val:
                    status = "empty_optional"
                else:
                    status = "ok"
                cells[col] = {"value": val, "status": status}
            row_dict["cells"] = cells

        result_rows.append(row_dict)

    return {
        "valid": report.valid,
        "errors": report.errors,
        "total_rows": len(report.rows),
        "headers": all_headers or [],
        "required_fields": (required_fields or []) + ["sample_alias"],
        "rows": result_rows,
    }


# Demo data per column — used to pre-fill template rows so users see the expected format
DEMO_VALUES: dict[str, list[str]] = {
    "sample_alias": ["SAMPLE_001", "SAMPLE_002"],
    "organism": ["Camelus dromedarius", "Camelus dromedarius"],
    "tax_id": ["9838", "9838"],
    "collection_date": ["2026-01-15", "2026-01-16"],
    "geographic_location": ["Saudi Arabia:Riyadh", "Saudi Arabia:Jeddah"],
    "breed": ["Arabian", "Arabian"],
    "host": ["Camelus dromedarius", "Camelus dromedarius"],
    "tissue": ["blood", "liver"],
    "sex": ["male", "female"],
    "developmental_stage": ["adult", "juvenile"],
    "isolation_source": ["nasopharyngeal swab", "blood"],
    "strain": ["MERS-CoV-SA-01", "MERS-CoV-SA-02"],
    "virus_identifier": ["VIRUS_001", "VIRUS_002"],
    "filename_forward": ["SAMPLE_001_R1.fastq.gz", "SAMPLE_002_R1.fastq.gz"],
    "filename_reverse": ["SAMPLE_001_R2.fastq.gz", "SAMPLE_002_R2.fastq.gz"],
    "md5_forward": ["d41d8cd98f00b204e9800998ecf8427e", "d41d8cd98f00b204e9800998ecf8427e"],
    "md5_reverse": ["d41d8cd98f00b204e9800998ecf8427e", "d41d8cd98f00b204e9800998ecf8427e"],
    "library_strategy": ["WGS", "WGS"],
    "platform": ["ILLUMINA", "ILLUMINA"],
    "instrument_model": ["Illumina NovaSeq 6000", "Illumina NovaSeq 6000"],
}


@router.get("/template/{checklist_id}")
async def download_bulk_template(checklist_id: str):
    """Download a bulk sample sheet template with demo data rows."""
    base_tsv = generate_template_tsv(checklist_id)
    if base_tsv is None:
        raise HTTPException(status_code=404, detail=f"Checklist '{checklist_id}' not found")

    schema = load_checklist(checklist_id)
    required = schema.get("required", [])
    optional = [k for k in schema.get("properties", {}).keys() if k not in required]
    checklist_cols = required + optional

    bulk_headers = ["sample_alias"] + checklist_cols + [
        c for c in BULK_EXTRA_COLUMNS if c != "sample_alias"
    ]

    import csv
    output = io.StringIO()
    writer = csv.writer(output, delimiter="\t")
    writer.writerow(bulk_headers)

    # Write 2 demo rows
    for row_idx in range(2):
        row = []
        for col in bulk_headers:
            demos = DEMO_VALUES.get(col, [])
            row.append(demos[row_idx] if row_idx < len(demos) else "")
        writer.writerow(row)

    tsv_content = output.getvalue()

    return StreamingResponse(
        io.BytesIO(tsv_content.encode("utf-8")),
        media_type="text/tab-separated-values",
        headers={
            "Content-Disposition": f'attachment; filename="{checklist_id}_bulk_template.tsv"'
        },
    )


@router.post("/validate")
async def validate_bulk_submit(
    file: UploadFile = File(...),
    checklist_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Validate an uploaded sample sheet TSV against staged files."""
    content = (await file.read()).decode("utf-8")
    svc = BulkSubmitService(db)
    parsed_rows = svc.parse_sample_sheet(content)
    if not parsed_rows:
        raise HTTPException(status_code=400, detail="No data rows found in sample sheet")

    # Get checklist required fields and all headers
    schema = load_checklist(checklist_id)
    required_fields = schema.get("required", []) if schema else []
    all_headers = list(parsed_rows[0].keys()) if parsed_rows else []

    validation = await svc.validate_sample_sheet(content, checklist_id, user.id)
    return _report_to_dict(validation, parsed_rows, required_fields, all_headers)


@router.post("/confirm")
async def confirm_bulk_submit(
    file: UploadFile = File(...),
    project_accession: str = Form(...),
    checklist_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Confirm and create all entities from a validated sample sheet."""
    content = (await file.read()).decode("utf-8")
    svc = BulkSubmitService(db)

    # Re-validate first
    report = await svc.validate_sample_sheet(content, checklist_id, user.id)
    if not report.valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Validation failed",
                "report": _report_to_dict(report),
            },
        )

    result = await svc.confirm_submission(
        content, project_accession, checklist_id, user.id, report
    )
    return result
