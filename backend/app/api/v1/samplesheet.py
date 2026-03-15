"""Generate nf-core-compatible samplesheets from SeqDB project data.

Supports multiple pipeline formats:
  - nf-core/fetchngs-style: sample,fastq_1,fastq_2
  - nf-core/sarek-style:    patient,sample,lane,fastq_1,fastq_2
  - snpchip (custom):       sample,idat_red,idat_grn,chip_type,organism
  - generic:                all metadata as flat CSV
"""

import csv
import io
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.project import Project
from app.models.sample import Sample
from app.models.experiment import Experiment
from app.models.run import Run

router = APIRouter(prefix="/samplesheet", tags=["samplesheet"])


class SamplesheetFormat(str, Enum):
    FETCHNGS = "fetchngs"
    SAREK = "sarek"
    RNASEQ = "rnaseq"
    SNPCHIP = "snpchip"
    GENERIC = "generic"


async def _load_project_tree(db: AsyncSession, accession: str) -> Project:
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
    return proj


def _download_url(run_accession: str, base_url: str) -> str:
    return f"{base_url}/api/v1/runs/{run_accession}/download"


def _build_fetchngs(proj: Project, base_url: str) -> list[dict]:
    """nf-core/fetchngs format: sample, fastq_1, fastq_2."""
    rows = []
    for sample in proj.samples:
        for exp in sample.experiments:
            runs = sorted(exp.runs, key=lambda r: r.file_path or "")
            if not runs:
                continue
            fastq_1 = _download_url(runs[0].internal_accession, base_url)
            fastq_2 = _download_url(runs[1].internal_accession, base_url) if len(runs) > 1 else ""
            rows.append({
                "sample": sample.internal_accession,
                "fastq_1": fastq_1,
                "fastq_2": fastq_2,
            })
    return rows


def _build_sarek(proj: Project, base_url: str) -> list[dict]:
    """nf-core/sarek format: patient, sample, lane, fastq_1, fastq_2."""
    rows = []
    for sample in proj.samples:
        for exp in sample.experiments:
            runs = sorted(exp.runs, key=lambda r: r.file_path or "")
            if not runs:
                continue
            fastq_1 = _download_url(runs[0].internal_accession, base_url)
            fastq_2 = _download_url(runs[1].internal_accession, base_url) if len(runs) > 1 else ""
            rows.append({
                "patient": proj.internal_accession,
                "sample": sample.internal_accession,
                "lane": exp.internal_accession,
                "fastq_1": fastq_1,
                "fastq_2": fastq_2,
            })
    return rows


def _build_rnaseq(proj: Project, base_url: str) -> list[dict]:
    """nf-core/rnaseq format: sample, fastq_1, fastq_2, strandedness."""
    rows = []
    for sample in proj.samples:
        for exp in sample.experiments:
            runs = sorted(exp.runs, key=lambda r: r.file_path or "")
            if not runs:
                continue
            fastq_1 = _download_url(runs[0].internal_accession, base_url)
            fastq_2 = _download_url(runs[1].internal_accession, base_url) if len(runs) > 1 else ""
            rows.append({
                "sample": sample.internal_accession,
                "fastq_1": fastq_1,
                "fastq_2": fastq_2,
                "strandedness": "auto",
            })
    return rows


def _build_snpchip(proj: Project, base_url: str) -> list[dict]:
    """SNP chip samplesheet: sample, organism, breed, files, chip metadata."""
    rows = []
    for sample in proj.samples:
        for exp in sample.experiments:
            runs = sorted(exp.runs, key=lambda r: r.file_path or "")
            idat_files = [r for r in runs if r.file_type and r.file_type.value == "IDAT"]
            other_files = [r for r in runs if not r.file_type or r.file_type.value != "IDAT"]

            row = {
                "sample": sample.internal_accession,
                "organism": sample.organism,
                "tax_id": sample.tax_id,
                "breed": sample.breed or "",
                "sex": sample.sex or "",
                "instrument_model": exp.instrument_model or "",
            }

            # IDAT files: expect Red and Grn pair
            if idat_files:
                red = next((r for r in idat_files if "_Red" in (r.file_path or "")), None)
                grn = next((r for r in idat_files if "_Grn" in (r.file_path or "")), None)
                row["idat_red"] = _download_url(red.internal_accession, base_url) if red else ""
                row["idat_grn"] = _download_url(grn.internal_accession, base_url) if grn else ""
            else:
                row["idat_red"] = ""
                row["idat_grn"] = ""

            # Other genotype files (BED/BIM/FAM, PED/MAP, VCF)
            for r in other_files:
                row.setdefault("genotype_file", _download_url(r.internal_accession, base_url))

            rows.append(row)
    return rows


def _build_generic(proj: Project, base_url: str) -> list[dict]:
    """Generic flat CSV with all metadata — works for any pipeline."""
    rows = []
    for sample in proj.samples:
        for exp in sample.experiments:
            for run in exp.runs:
                rows.append({
                    "project_accession": proj.internal_accession,
                    "sample_accession": sample.internal_accession,
                    "experiment_accession": exp.internal_accession,
                    "run_accession": run.internal_accession,
                    "organism": sample.organism,
                    "tax_id": sample.tax_id,
                    "breed": sample.breed or "",
                    "sex": sample.sex or "",
                    "collection_date": str(sample.collection_date) if sample.collection_date else "",
                    "geographic_location": sample.geographic_location or "",
                    "platform": exp.platform.value if hasattr(exp.platform, "value") else str(exp.platform),
                    "instrument_model": exp.instrument_model or "",
                    "library_strategy": exp.library_strategy.value if hasattr(exp.library_strategy, "value") else str(exp.library_strategy),
                    "library_layout": exp.library_layout.value if hasattr(exp.library_layout, "value") else str(exp.library_layout),
                    "file_type": run.file_type.value if hasattr(run.file_type, "value") else str(run.file_type),
                    "filename": (run.file_path or "").rsplit("/", 1)[-1],
                    "file_size": run.file_size,
                    "checksum_md5": run.checksum_md5 or "",
                    "download_url": _download_url(run.internal_accession, base_url),
                })
    return rows


FORMAT_BUILDERS = {
    SamplesheetFormat.FETCHNGS: _build_fetchngs,
    SamplesheetFormat.SAREK: _build_sarek,
    SamplesheetFormat.RNASEQ: _build_rnaseq,
    SamplesheetFormat.SNPCHIP: _build_snpchip,
    SamplesheetFormat.GENERIC: _build_generic,
}


@router.get("/{project_accession}")
async def generate_samplesheet(
    project_accession: str,
    format: SamplesheetFormat = Query(
        SamplesheetFormat.GENERIC,
        description="Samplesheet format: fetchngs, sarek, rnaseq, snpchip, generic",
    ),
    db: AsyncSession = Depends(get_db),
):
    """Generate a pipeline-ready samplesheet CSV for a project.

    Usage examples:
      curl .../samplesheet/NFDP-PRJ-000001?format=fetchngs > samplesheet.csv
      curl .../samplesheet/NFDP-PRJ-000001?format=snpchip > samples.csv
      curl .../samplesheet/NFDP-PRJ-000001?format=sarek > input.csv
    """
    proj = await _load_project_tree(db, project_accession)
    builder = FORMAT_BUILDERS[format]
    rows = builder(proj, "")

    if not rows:
        raise HTTPException(status_code=404, detail="No runs found for this project")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={project_accession}_{format.value}_samplesheet.csv"
        },
    )
