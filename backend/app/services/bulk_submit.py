"""Bulk submit service: parse sample sheets, validate, match files, create entities."""

import csv
import io
import re
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.staging import StagingService
from app.services.samples import create_sample
from app.services.experiments import create_experiment
from app.services.runs import create_run
from app.services.validation import load_checklist
from app.schemas.sample import SampleCreate
from app.schemas.experiment import ExperimentCreate


@dataclass
class FileMatch:
    staged_file_id: int
    filename: str
    md5: str
    direction: str  # "forward" or "reverse"


@dataclass
class RowValidation:
    row_num: int
    sample_alias: str
    errors: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)
    forward_file: FileMatch | None = None
    reverse_file: FileMatch | None = None


@dataclass
class ValidationReport:
    valid: bool
    rows: list[RowValidation] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)


def _find_closest(target: str, candidates: list[str]) -> str | None:
    """Find the closest matching filename using simple substring + length similarity."""
    if not candidates:
        return None
    target_lower = target.lower()
    best, best_score = None, 0
    for c in candidates:
        c_lower = c.lower()
        # Count matching characters in order (simple similarity)
        score = 0
        j = 0
        for ch in target_lower:
            idx = c_lower.find(ch, j)
            if idx >= 0:
                score += 1
                j = idx + 1
        # Normalize by max length
        norm = score / max(len(target), len(c), 1)
        if norm > best_score:
            best_score = norm
            best = c
    # Only suggest if reasonably similar (>60%)
    return best if best_score > 0.6 else None


FILE_EXT_MAP = {
    ".fastq": "FASTQ",
    ".fastq.gz": "FASTQ",
    ".fq": "FASTQ",
    ".fq.gz": "FASTQ",
    ".bam": "BAM",
    ".cram": "CRAM",
    ".vcf": "VCF",
    ".vcf.gz": "VCF",
}


def _detect_file_type(filename: str) -> str:
    """Detect file type from filename extension."""
    lower = filename.lower()
    for ext, ftype in FILE_EXT_MAP.items():
        if lower.endswith(ext):
            return ftype
    return "OTHER"


class BulkSubmitService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.staging = StagingService(db)

    def parse_sample_sheet(self, tsv_content: str) -> list[dict]:
        """Parse a TSV sample sheet into a list of row dicts."""
        reader = csv.DictReader(io.StringIO(tsv_content), delimiter="\t")
        return list(reader)

    def validate_row(
        self, row: dict, row_num: int, required_fields: list[str]
    ) -> list[dict]:
        """Check that required fields are present and non-empty in a row."""
        errors = []
        for f in required_fields:
            val = row.get(f, "").strip() if row.get(f) else ""
            if not val:
                errors.append({
                    "row": row_num,
                    "field": f,
                    "message": f"Required field '{f}' is missing or empty",
                })
        return errors

    async def validate_sample_sheet(
        self,
        tsv_content: str,
        checklist_id: str,
        user_id: int,
    ) -> ValidationReport:
        """Full validation of a sample sheet against a checklist and staged files."""
        rows = self.parse_sample_sheet(tsv_content)
        if not rows:
            return ValidationReport(
                valid=False, errors=[{"field": "file", "message": "No data rows found"}]
            )

        schema = load_checklist(checklist_id)
        if schema is None:
            return ValidationReport(
                valid=False,
                errors=[{"field": "checklist_id", "message": f"Checklist '{checklist_id}' not found"}],
            )

        required_fields = schema.get("required", [])
        headers = list(rows[0].keys()) if rows else []
        has_explicit_files = "filename_forward" in headers

        report = ValidationReport(valid=True)

        for i, row in enumerate(rows, start=2):
            alias = row.get("sample_alias", "").strip()
            rv = RowValidation(row_num=i, sample_alias=alias)

            # Validate required fields
            field_errors = self.validate_row(row, i, required_fields)
            if not alias:
                field_errors.append({
                    "row": i,
                    "field": "sample_alias",
                    "message": "Required field 'sample_alias' is missing or empty",
                })
            rv.errors.extend(field_errors)

            # Fetch all staged files once (cached per-user for suggestions)
            if not hasattr(self, "_all_staged"):
                self._all_staged = await self.staging.list_files(user_id)

            # Match files — try explicit filenames first, fall back to alias pattern
            fwd_name = row.get("filename_forward", "").strip() if has_explicit_files else ""
            rev_name = row.get("filename_reverse", "").strip() if has_explicit_files else ""

            # Helper: find staged file by exact name, then by MD5
            async def match_file(
                declared_name: str, md5_col: str, direction: str
            ) -> FileMatch | None:
                if declared_name:
                    staged = await self.staging.find_by_filename(declared_name, user_id)
                    if staged:
                        # MD5 check
                        expected_md5 = row.get(md5_col, "").strip()
                        if expected_md5 and staged.checksum_md5 and expected_md5 != staged.checksum_md5:
                            rv.warnings.append({
                                "row": i, "field": md5_col,
                                "message": f"MD5 mismatch: sheet={expected_md5}, staged={staged.checksum_md5}",
                            })
                        return FileMatch(
                            staged_file_id=staged.id, filename=staged.filename,
                            md5=staged.checksum_md5, direction=direction,
                        )
                    # Exact name not found — try MD5 matching
                    expected_md5 = row.get(md5_col, "").strip()
                    if expected_md5:
                        for sf in self._all_staged:
                            if sf.checksum_md5 == expected_md5:
                                rv.warnings.append({
                                    "row": i, "field": f"filename_{direction}",
                                    "message": (
                                        f"'{declared_name}' not found but matched by MD5 "
                                        f"to staged file '{sf.filename}'"
                                    ),
                                })
                                return FileMatch(
                                    staged_file_id=sf.id, filename=sf.filename,
                                    md5=sf.checksum_md5, direction=direction,
                                )
                return None

            rv.forward_file = await match_file(fwd_name, "md5_forward", "forward")
            rv.reverse_file = await match_file(rev_name, "md5_reverse", "reverse")

            # Fall back to alias-based pattern matching
            if alias and (not rv.forward_file or not rv.reverse_file):
                candidates = await self.staging.find_by_alias(alias, user_id)
                for c in candidates:
                    if not rv.forward_file and re.search(
                        rf"{re.escape(alias)}[._-]R1", c.filename, re.IGNORECASE
                    ):
                        rv.forward_file = FileMatch(
                            staged_file_id=c.id, filename=c.filename,
                            md5=c.checksum_md5, direction="forward",
                        )
                        if fwd_name:
                            rv.warnings.append({
                                "row": i, "field": "filename_forward",
                                "message": f"'{fwd_name}' not found, auto-matched to '{c.filename}' by alias pattern",
                            })
                    elif not rv.reverse_file and re.search(
                        rf"{re.escape(alias)}[._-]R2", c.filename, re.IGNORECASE
                    ):
                        rv.reverse_file = FileMatch(
                            staged_file_id=c.id, filename=c.filename,
                            md5=c.checksum_md5, direction="reverse",
                        )
                        if rev_name:
                            rv.warnings.append({
                                "row": i, "field": "filename_reverse",
                                "message": f"'{rev_name}' not found, auto-matched to '{c.filename}' by alias pattern",
                            })

            # If still not found, give helpful error with closest match suggestion
            if not rv.forward_file and (fwd_name or alias):
                suggestion = _find_closest(
                    fwd_name or f"{alias}_R1",
                    [sf.filename for sf in self._all_staged],
                )
                msg = f"Staged file '{fwd_name or alias + '_R1.*'}' not found"
                if suggestion:
                    msg += f". Did you mean '{suggestion}'?"
                rv.errors.append({"row": i, "field": "filename_forward", "message": msg})

            if not rv.reverse_file and rev_name:
                suggestion = _find_closest(
                    rev_name, [sf.filename for sf in self._all_staged],
                )
                msg = f"Staged file '{rev_name}' not found"
                if suggestion:
                    msg += f". Did you mean '{suggestion}'?"
                rv.errors.append({"row": i, "field": "filename_reverse", "message": msg})

            if rv.errors:
                report.valid = False
            report.rows.append(rv)

        return report

    async def confirm_submission(
        self,
        tsv_content: str,
        project_accession: str,
        checklist_id: str,
        user_id: int,
        report: ValidationReport,
    ) -> dict:
        """Create all entities from a validated sample sheet."""
        rows = self.parse_sample_sheet(tsv_content)
        samples_created = []
        experiments_created = []
        runs_created = []
        file_ids_to_link = []

        for row, rv in zip(rows, report.rows):
            if rv.errors:
                continue

            # Create sample
            raw_date = (row.get("collection_date") or "").strip()
            sample_data = SampleCreate(
                project_accession=project_accession,
                checklist_id=checklist_id,
                organism=row.get("organism") or "unknown",
                tax_id=int(row.get("tax_id") or 0),
                collection_date=raw_date if raw_date else None,
                geographic_location=row.get("geographic_location") or None,
                breed=row.get("breed") or None,
                host=row.get("host") or None,
                tissue=row.get("tissue") or None,
                developmental_stage=row.get("developmental_stage") or None,
                sex=row.get("sex") or None,
            )
            sample = await create_sample(self.db, sample_data)
            samples_created.append(sample.internal_accession)

            # Create experiment
            exp_data = ExperimentCreate(
                sample_accession=sample.internal_accession,
                platform=row.get("platform") or "ILLUMINA",
                instrument_model=row.get("instrument_model") or "unspecified",
                library_strategy=row.get("library_strategy") or "WGS",
                library_source=row.get("library_source") or "GENOMIC",
                library_layout=row.get("library_layout") or "PAIRED",
                insert_size=int(row["insert_size"]) if row.get("insert_size") else None,
            )
            experiment = await create_experiment(self.db, exp_data)
            experiments_created.append(experiment.internal_accession)

            # Create runs for matched files
            for fm in [rv.forward_file, rv.reverse_file]:
                if fm is None:
                    continue
                file_type = _detect_file_type(fm.filename)
                run = await create_run(
                    self.db,
                    experiment_accession=experiment.internal_accession,
                    file_type=file_type,
                    file_path=fm.filename,
                    file_size=0,  # size tracked in staged_file
                    checksum_md5=fm.md5,
                )
                runs_created.append(run.internal_accession)
                file_ids_to_link.append(fm.staged_file_id)

        # Mark staged files as linked
        await self.staging.mark_linked(file_ids_to_link)

        return {
            "status": "created",
            "samples": samples_created,
            "experiments": experiments_created,
            "runs": runs_created,
        }
