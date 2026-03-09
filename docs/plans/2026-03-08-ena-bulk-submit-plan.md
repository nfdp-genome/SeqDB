# ENA-Style Bulk Submit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an ENA-style bulk submission mode with file staging, MD5 validation, and sample sheet-driven entity creation alongside the existing quick submit wizard.

**Architecture:** Two submission modes on `/submit` — Quick Submit (existing wizard, renamed Study→Project) and Bulk Submit (upload files to staging, upload sample sheet, validate+link by MD5, create entities atomically). Files land in MinIO staging bucket via browser or FTP, then move to archive on confirmation.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, Alembic, MinIO (minio-py), Next.js 16, React Query, shadcn/ui, Tailwind CSS v4

---

### Task 1: Rename Study → Project in Backend Models

**Files:**
- Modify: `backend/app/models/study.py` → rename to `backend/app/models/project.py`
- Modify: `backend/app/models/enums.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/models/sample.py` (foreign key reference)
- Modify: `backend/app/models/submission.py` (foreign key reference)

**Step 1: Rename the model file and class**

Copy `backend/app/models/study.py` to `backend/app/models/project.py`. Update the class:

```python
# backend/app/models/project.py
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, date
from app.database import Base
from app.models.enums import ProjectType


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    internal_accession: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    ena_accession: Mapped[str | None] = mapped_column(String(20), nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_type: Mapped[ProjectType] = mapped_column(SAEnum(ProjectType))
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    license: Mapped[str] = mapped_column(String(20), default="CC-BY")
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by_user = relationship("User", back_populates="projects")
    samples = relationship("Sample", back_populates="project")
```

**Step 2: Update Sample model foreign key**

In `backend/app/models/sample.py`, change:
- `study_id` → `project_id`, ForeignKey `"projects.id"`
- `study` relationship → `project`, back_populates `"samples"`

**Step 3: Update Submission model**

In `backend/app/models/submission.py`, change:
- `study_id` → `project_id`, ForeignKey `"projects.id"`

**Step 4: Update User model**

In `backend/app/models/user.py`, change:
- `studies` relationship → `projects`, back_populates `"created_by_user"`

**Step 5: Delete old study.py, update __init__.py**

Remove `backend/app/models/study.py`. Update imports in `__init__.py` to use `Project` from `project`.

**Step 6: Run tests to see what breaks**

Run: `cd backend && python -m pytest tests/ -x -v 2>&1 | head -50`
Expected: Many failures referencing `Study` — this confirms what needs updating next.

**Step 7: Commit**

```bash
git add backend/app/models/
git commit -m "refactor: rename Study model to Project"
```

---

### Task 2: Rename Study → Project in Backend Schemas

**Files:**
- Modify: `backend/app/schemas/study.py` → rename to `backend/app/schemas/project.py`
- Modify: `backend/app/schemas/submission.py`

**Step 1: Rename schema file and classes**

Copy `backend/app/schemas/study.py` to `backend/app/schemas/project.py`. Rename:
- `StudyCreate` → `ProjectCreate`
- `StudyResponse` → `ProjectResponse`
- Field `study_accession` references → `project_accession` where applicable

```python
# backend/app/schemas/project.py
from pydantic import BaseModel
from datetime import date, datetime
from app.models.enums import ProjectType


class ProjectCreate(BaseModel):
    title: str
    description: str | None = None
    project_type: ProjectType
    release_date: date | None = None
    license: str = "CC-BY"


class ProjectResponse(BaseModel):
    accession: str
    ena_accession: str | None = None
    title: str
    description: str | None = None
    project_type: ProjectType
    release_date: date | None = None
    license: str
    created_at: datetime

    model_config = {"from_attributes": True}
```

**Step 2: Update submission schema**

In `backend/app/schemas/submission.py`, rename `study_accession` → `project_accession`.

**Step 3: Update sample schema**

In `backend/app/schemas/sample.py`, rename `study_accession` → `project_accession`.

**Step 4: Delete old study.py schema**

**Step 5: Commit**

```bash
git add backend/app/schemas/
git commit -m "refactor: rename Study schemas to Project"
```

---

### Task 3: Rename Study → Project in Backend Services

**Files:**
- Modify: `backend/app/services/studies.py` → rename to `backend/app/services/projects.py`
- Modify: `backend/app/services/samples.py`
- Modify: `backend/app/services/submissions.py`
- Modify: `backend/app/services/accession.py`

**Step 1: Rename service file and functions**

Copy `backend/app/services/studies.py` to `backend/app/services/projects.py`. Rename:
- `create_study` → `create_project`
- `get_study_by_accession` → `get_project_by_accession`
- `list_studies` → `list_projects`
- All `Study` model references → `Project`

**Step 2: Update samples service**

In `backend/app/services/samples.py`, change `study_accession` → `project_accession`, import `Project` instead of `Study`.

**Step 3: Update submissions service**

In `backend/app/services/submissions.py`, change all Study references to Project.

**Step 4: Update accession service**

In `backend/app/services/accession.py`, rename `STUDY` → `PROJECT` in AccessionType if present (the prefix "PRJ" stays).

**Step 5: Delete old studies.py service**

**Step 6: Commit**

```bash
git add backend/app/services/
git commit -m "refactor: rename Study services to Project"
```

---

### Task 4: Rename Study → Project in Backend API Endpoints

**Files:**
- Modify: `backend/app/api/v1/studies.py` → rename to `backend/app/api/v1/projects.py`
- Modify: `backend/app/api/v1/router.py`
- Modify: `backend/app/api/v1/submissions.py`
- Modify: `backend/app/api/v1/samples.py`
- Modify: `backend/app/api/v1/search.py`
- Modify: `backend/app/api/v1/templates.py`

**Step 1: Rename API file**

Copy `backend/app/api/v1/studies.py` to `backend/app/api/v1/projects.py`. Update:
- Router prefix: `/studies` → `/projects`
- Tags: `["studies"]` → `["projects"]`
- Import `ProjectCreate`, `ProjectResponse`, `create_project`, etc.
- Function names: `_study_to_response` → `_project_to_response`

**Step 2: Update router.py**

Replace `studies_router` import with `projects_router` from `projects`.

**Step 3: Update all other API files**

In samples.py, submissions.py, search.py, templates.py — change `study_accession` → `project_accession` in request/response bodies and query params.

**Step 4: Delete old studies.py API file**

**Step 5: Run all tests**

Run: `cd backend && python -m pytest tests/ -x -v 2>&1 | head -80`
Expected: Failures in tests still referencing `/studies` — fix in next task.

**Step 6: Commit**

```bash
git add backend/app/api/
git commit -m "refactor: rename Study API endpoints to Project (/projects)"
```

---

### Task 5: Update Backend Tests for Study → Project Rename

**Files:**
- Modify: `backend/tests/test_integration.py`
- Modify: `backend/tests/test_templates.py`
- Modify: `backend/tests/test_minio_upload.py`
- Modify: `backend/tests/conftest.py` (if references Study)

**Step 1: Find and replace in all test files**

In every test file:
- `/api/v1/studies` → `/api/v1/projects`
- `study_accession` → `project_accession`
- `study_acc` → `project_acc`
- `"Study"` → `"Project"` in test names/descriptions

**Step 2: Run all tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All tests pass with renamed endpoints.

**Step 3: Commit**

```bash
git add backend/tests/
git commit -m "test: update all tests for Study → Project rename"
```

---

### Task 6: Create Alembic Migration for Study → Project Rename

**Files:**
- Create: `backend/alembic/versions/XXXX_rename_studies_to_projects.py`

**Step 1: Generate migration**

Run: `cd backend && alembic revision --autogenerate -m "rename studies to projects"`

If autogenerate doesn't detect the rename (it usually creates drop+create), write manually:

```python
def upgrade():
    op.rename_table("studies", "projects")
    # Update foreign keys
    op.alter_column("samples", "study_id", new_column_name="project_id")
    op.alter_column("submissions", "study_id", new_column_name="project_id")

def downgrade():
    op.alter_column("submissions", "project_id", new_column_name="study_id")
    op.alter_column("samples", "project_id", new_column_name="study_id")
    op.rename_table("projects", "studies")
```

**Step 2: Run migration**

Run: `cd backend && alembic upgrade head`
Expected: Migration applies without errors.

**Step 3: Verify database**

Run: `psql -U nfdp -d nfdp -c "\dt"` — should show `projects` table, no `studies`.

**Step 4: Commit**

```bash
git add backend/alembic/
git commit -m "migrate: rename studies table to projects"
```

---

### Task 7: Add `staged_files` Model and Migration

**Files:**
- Create: `backend/app/models/staged_file.py`
- Modify: `backend/app/models/enums.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: Add new enums**

In `backend/app/models/enums.py`, add:

```python
class UploadMethod(str, enum.Enum):
    BROWSER = "browser"
    FTP = "ftp"

class StagedFileStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    LINKED = "linked"
    EXPIRED = "expired"
```

**Step 2: Create the model**

```python
# backend/app/models/staged_file.py
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timedelta
from app.database import Base
from app.models.enums import UploadMethod, StagedFileStatus


class StagedFile(Base):
    __tablename__ = "staged_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String(500))
    file_size: Mapped[int] = mapped_column(BigInteger)
    checksum_md5: Mapped[str] = mapped_column(String(32))
    upload_method: Mapped[UploadMethod] = mapped_column(SAEnum(UploadMethod))
    staging_path: Mapped[str] = mapped_column(String(1000))
    status: Mapped[StagedFileStatus] = mapped_column(
        SAEnum(StagedFileStatus), default=StagedFileStatus.PENDING
    )
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.utcnow() + timedelta(days=7)
    )

    user = relationship("User")
```

**Step 3: Update __init__.py**

Add `from app.models.staged_file import StagedFile`.

**Step 4: Generate and run migration**

Run:
```bash
cd backend && alembic revision --autogenerate -m "add staged_files table"
alembic upgrade head
```

**Step 5: Verify**

Run: `psql -U nfdp -d nfdp -c "\d staged_files"` — should show the table.

**Step 6: Commit**

```bash
git add backend/app/models/ backend/alembic/
git commit -m "feat: add staged_files model and migration"
```

---

### Task 8: Create Staging Service

**Files:**
- Create: `backend/app/services/staging.py`
- Create: `backend/tests/test_staging.py`

**Step 1: Write the tests**

```python
# backend/tests/test_staging.py
import pytest
from app.services.staging import StagingService


@pytest.mark.asyncio
async def test_list_staged_files_empty(db_session, test_user):
    svc = StagingService(db_session)
    files = await svc.list_files(test_user.id)
    assert files == []


@pytest.mark.asyncio
async def test_register_staged_file(db_session, test_user):
    svc = StagingService(db_session)
    sf = await svc.register_file(
        user_id=test_user.id,
        filename="sample1_R1.fastq.gz",
        file_size=1024000,
        checksum_md5="abc123def456abc123def456abc123de",
        upload_method="browser",
        staging_path="nfdp-staging/1/sample1_R1.fastq.gz",
    )
    assert sf.filename == "sample1_R1.fastq.gz"
    assert sf.status.value == "pending"

    files = await svc.list_files(test_user.id)
    assert len(files) == 1


@pytest.mark.asyncio
async def test_delete_staged_file(db_session, test_user):
    svc = StagingService(db_session)
    sf = await svc.register_file(
        user_id=test_user.id,
        filename="temp.fastq.gz",
        file_size=512,
        checksum_md5="aaaabbbbccccddddaaaabbbbccccdddd",
        upload_method="browser",
        staging_path="nfdp-staging/1/temp.fastq.gz",
    )
    result = await svc.delete_file(sf.id, test_user.id)
    assert result is True

    files = await svc.list_files(test_user.id)
    assert len(files) == 0


@pytest.mark.asyncio
async def test_find_files_by_alias(db_session, test_user):
    svc = StagingService(db_session)
    await svc.register_file(
        user_id=test_user.id,
        filename="SAMPLE01_R1.fastq.gz",
        file_size=1024,
        checksum_md5="aaaa1111bbbb2222cccc3333dddd4444",
        upload_method="browser",
        staging_path="nfdp-staging/1/SAMPLE01_R1.fastq.gz",
    )
    await svc.register_file(
        user_id=test_user.id,
        filename="SAMPLE01_R2.fastq.gz",
        file_size=1024,
        checksum_md5="eeee5555ffff6666aaaa7777bbbb8888",
        upload_method="browser",
        staging_path="nfdp-staging/1/SAMPLE01_R2.fastq.gz",
    )

    matches = await svc.find_by_alias("SAMPLE01", test_user.id)
    assert len(matches) == 2
    names = {m.filename for m in matches}
    assert "SAMPLE01_R1.fastq.gz" in names
    assert "SAMPLE01_R2.fastq.gz" in names
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_staging.py -v`
Expected: ImportError — `app.services.staging` does not exist.

**Step 3: Implement StagingService**

```python
# backend/app/services/staging.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.staged_file import StagedFile
from app.models.enums import UploadMethod, StagedFileStatus
from app.services.storage import StorageService


BUCKET_STAGING = "nfdp-staging"


class StagingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_file(
        self,
        user_id: int,
        filename: str,
        file_size: int,
        checksum_md5: str,
        upload_method: str,
        staging_path: str,
    ) -> StagedFile:
        sf = StagedFile(
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            checksum_md5=checksum_md5,
            upload_method=UploadMethod(upload_method),
            staging_path=staging_path,
        )
        self.db.add(sf)
        await self.db.commit()
        await self.db.refresh(sf)
        return sf

    async def list_files(self, user_id: int) -> list[StagedFile]:
        result = await self.db.execute(
            select(StagedFile)
            .where(StagedFile.user_id == user_id)
            .where(StagedFile.status != StagedFileStatus.EXPIRED)
            .order_by(StagedFile.uploaded_at.desc())
        )
        return list(result.scalars().all())

    async def delete_file(self, file_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            delete(StagedFile)
            .where(StagedFile.id == file_id)
            .where(StagedFile.user_id == user_id)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def find_by_alias(self, alias: str, user_id: int) -> list[StagedFile]:
        """Find staged files matching {alias}_R1.* or {alias}_R2.* pattern."""
        result = await self.db.execute(
            select(StagedFile)
            .where(StagedFile.user_id == user_id)
            .where(StagedFile.status != StagedFileStatus.EXPIRED)
            .where(StagedFile.filename.ilike(f"{alias}_%"))
        )
        return list(result.scalars().all())

    async def find_by_filename(self, filename: str, user_id: int) -> StagedFile | None:
        result = await self.db.execute(
            select(StagedFile)
            .where(StagedFile.user_id == user_id)
            .where(StagedFile.filename == filename)
            .where(StagedFile.status != StagedFileStatus.EXPIRED)
        )
        return result.scalar_one_or_none()

    async def mark_linked(self, file_ids: list[int]) -> None:
        for fid in file_ids:
            result = await self.db.execute(
                select(StagedFile).where(StagedFile.id == fid)
            )
            sf = result.scalar_one_or_none()
            if sf:
                sf.status = StagedFileStatus.LINKED
        await self.db.commit()

    def generate_presigned_upload_url(self, user_id: int, filename: str) -> tuple[str, str]:
        """Returns (staging_path, presigned_url)."""
        staging_path = f"{user_id}/{filename}"
        storage = StorageService()
        storage.ensure_buckets()
        url = storage.generate_presigned_upload_url(BUCKET_STAGING, staging_path)
        return staging_path, url
```

**Step 4: Run tests**

Run: `cd backend && python -m pytest tests/test_staging.py -v`
Expected: All 4 tests pass.

**Step 5: Commit**

```bash
git add backend/app/services/staging.py backend/tests/test_staging.py
git commit -m "feat: add StagingService for file staging management"
```

---

### Task 9: Create Staging API Endpoints

**Files:**
- Create: `backend/app/api/v1/staging.py`
- Create: `backend/app/schemas/staging.py`
- Modify: `backend/app/api/v1/router.py`

**Step 1: Create schemas**

```python
# backend/app/schemas/staging.py
from pydantic import BaseModel
from datetime import datetime


class StagingInitiateRequest(BaseModel):
    filename: str
    file_size: int


class StagingInitiateResponse(BaseModel):
    staged_file_id: int
    presigned_url: str
    staging_path: str
    expires_in: int = 86400


class StagedFileResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    checksum_md5: str
    upload_method: str
    status: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}
```

**Step 2: Create API endpoints**

```python
# backend/app/api/v1/staging.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.schemas.staging import StagingInitiateRequest, StagingInitiateResponse, StagedFileResponse
from app.services.staging import StagingService

router = APIRouter(prefix="/staging", tags=["staging"])


@router.post("/initiate", response_model=StagingInitiateResponse)
async def initiate_staging_upload(
    req: StagingInitiateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = StagingService(db)
    staging_path, presigned_url = svc.generate_presigned_upload_url(user.id, req.filename)
    sf = await svc.register_file(
        user_id=user.id,
        filename=req.filename,
        file_size=req.file_size,
        checksum_md5="",  # Will be computed after upload
        upload_method="browser",
        staging_path=staging_path,
    )
    return StagingInitiateResponse(
        staged_file_id=sf.id,
        presigned_url=presigned_url,
        staging_path=staging_path,
    )


@router.get("/files", response_model=list[StagedFileResponse])
async def list_staged_files(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = StagingService(db)
    files = await svc.list_files(user.id)
    return [StagedFileResponse(
        id=f.id,
        filename=f.filename,
        file_size=f.file_size,
        checksum_md5=f.checksum_md5,
        upload_method=f.upload_method.value,
        status=f.status.value,
        uploaded_at=f.uploaded_at,
    ) for f in files]


@router.delete("/files/{file_id}")
async def delete_staged_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = StagingService(db)
    deleted = await svc.delete_file(file_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": "deleted"}
```

**Step 3: Register in router**

In `backend/app/api/v1/router.py`, add:
```python
from app.api.v1.staging import router as staging_router
api_router.include_router(staging_router)
```

**Step 4: Run tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All existing + staging tests pass.

**Step 5: Commit**

```bash
git add backend/app/api/v1/staging.py backend/app/schemas/staging.py backend/app/api/v1/router.py
git commit -m "feat: add staging API endpoints (initiate, list, delete)"
```

---

### Task 10: Create Bulk Submit Service

**Files:**
- Create: `backend/app/services/bulk_submit.py`
- Create: `backend/tests/test_bulk_submit.py`

**Step 1: Write the tests**

```python
# backend/tests/test_bulk_submit.py
import pytest
from app.services.bulk_submit import BulkSubmitService, ValidationReport


def test_parse_sample_sheet_with_explicit_files():
    tsv = (
        "sample_alias\torganism\ttax_id\tcollection_date\tgeographic_location"
        "\tfilename_forward\tfilename_reverse\tmd5_forward\tmd5_reverse"
        "\tlibrary_strategy\tplatform\n"
        "CAMEL01\tCamelus dromedarius\t9838\t2026-03-01\tSaudi Arabia:Riyadh"
        "\tCAMEL01_R1.fastq.gz\tCAMEL01_R2.fastq.gz\taabbccdd11223344aabbccdd11223344\teeff0011aabbccdd22334455eeff0011"
        "\tWGS\tILLUMINA\n"
    )
    svc = BulkSubmitService.__new__(BulkSubmitService)
    rows = svc.parse_sample_sheet(tsv)
    assert len(rows) == 1
    assert rows[0]["sample_alias"] == "CAMEL01"
    assert rows[0]["filename_forward"] == "CAMEL01_R1.fastq.gz"


def test_parse_sample_sheet_without_file_columns():
    tsv = (
        "sample_alias\torganism\ttax_id\tcollection_date\tgeographic_location\n"
        "GOAT01\tCapra hircus\t9925\t2026-03-02\tSaudi Arabia:AlUla\n"
    )
    svc = BulkSubmitService.__new__(BulkSubmitService)
    rows = svc.parse_sample_sheet(tsv)
    assert len(rows) == 1
    assert rows[0]["sample_alias"] == "GOAT01"
    assert "filename_forward" not in rows[0]


def test_validate_row_missing_required_field():
    svc = BulkSubmitService.__new__(BulkSubmitService)
    errors = svc.validate_row(
        row={"sample_alias": "X", "organism": "Test", "collection_date": "2026-01-01"},
        row_num=2,
        required_fields=["sample_alias", "organism", "tax_id", "collection_date", "geographic_location"],
    )
    assert len(errors) == 2  # tax_id and geographic_location missing
    assert any(e["field"] == "tax_id" for e in errors)
    assert any(e["field"] == "geographic_location" for e in errors)
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_bulk_submit.py -v`
Expected: ImportError.

**Step 3: Implement BulkSubmitService**

```python
# backend/app/services/bulk_submit.py
import csv
import io
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.staging import StagingService
from app.services.samples import create_sample
from app.services.experiments import create_experiment
from app.services.runs import create_run
from app.services.storage import StorageService
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


class BulkSubmitService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def parse_sample_sheet(self, tsv_content: str) -> list[dict]:
        reader = csv.DictReader(io.StringIO(tsv_content), delimiter="\t")
        rows = []
        for row in reader:
            cleaned = {k.strip(): v.strip() for k, v in row.items() if v and v.strip()}
            rows.append(cleaned)
        return rows

    def validate_row(self, row: dict, row_num: int, required_fields: list[str]) -> list[dict]:
        errors = []
        for f in required_fields:
            if f not in row or not row[f]:
                errors.append({"row": row_num, "field": f, "message": f"Missing required field: {f}"})
        return errors

    async def validate_sample_sheet(
        self,
        tsv_content: str,
        checklist_id: str,
        user_id: int,
    ) -> ValidationReport:
        rows = self.parse_sample_sheet(tsv_content)
        if not rows:
            return ValidationReport(valid=False, errors=[{"row": 0, "field": "", "message": "Empty sample sheet"}])

        # Load checklist for required fields
        schema = load_checklist(checklist_id)
        required_fields = ["sample_alias"] + (schema.get("required", []) if schema else [])

        staging_svc = StagingService(self.db)
        report = ValidationReport(valid=True)

        for i, row in enumerate(rows, start=2):
            alias = row.get("sample_alias", f"row_{i}")
            rv = RowValidation(row_num=i, sample_alias=alias)

            # Validate required fields
            field_errors = self.validate_row(row, i, required_fields)
            if field_errors:
                rv.errors.extend(field_errors)
                report.valid = False

            # Match files
            has_explicit = "filename_forward" in row
            if has_explicit:
                fwd = await staging_svc.find_by_filename(row["filename_forward"], user_id)
                if not fwd:
                    rv.errors.append({"row": i, "field": "filename_forward",
                                      "message": f"File '{row['filename_forward']}' not found in staging"})
                    report.valid = False
                else:
                    # MD5 check
                    if "md5_forward" in row and fwd.checksum_md5 and row["md5_forward"] != fwd.checksum_md5:
                        rv.errors.append({"row": i, "field": "md5_forward",
                                          "message": f"MD5 mismatch: expected {row['md5_forward']}, got {fwd.checksum_md5}"})
                        report.valid = False
                    else:
                        rv.forward_file = FileMatch(fwd.id, fwd.filename, fwd.checksum_md5, "forward")

                if "filename_reverse" in row and row["filename_reverse"]:
                    rev = await staging_svc.find_by_filename(row["filename_reverse"], user_id)
                    if not rev:
                        rv.errors.append({"row": i, "field": "filename_reverse",
                                          "message": f"File '{row['filename_reverse']}' not found in staging"})
                        report.valid = False
                    else:
                        if "md5_reverse" in row and rev.checksum_md5 and row["md5_reverse"] != rev.checksum_md5:
                            rv.errors.append({"row": i, "field": "md5_reverse",
                                              "message": f"MD5 mismatch: expected {row['md5_reverse']}, got {rev.checksum_md5}"})
                            report.valid = False
                        else:
                            rv.reverse_file = FileMatch(rev.id, rev.filename, rev.checksum_md5, "reverse")
            else:
                # Auto-detect by naming convention
                matches = await staging_svc.find_by_alias(alias, user_id)
                for m in matches:
                    lower = m.filename.lower()
                    if "_r1" in lower or "_1." in lower:
                        rv.forward_file = FileMatch(m.id, m.filename, m.checksum_md5, "forward")
                    elif "_r2" in lower or "_2." in lower:
                        rv.reverse_file = FileMatch(m.id, m.filename, m.checksum_md5, "reverse")

                if not rv.forward_file:
                    rv.errors.append({"row": i, "field": "file",
                                      "message": f"No forward read file found for alias '{alias}'. Upload {alias}_R1.fastq.gz or specify filename_forward column."})
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
        """Create all entities and move files from staging to archive."""
        rows = self.parse_sample_sheet(tsv_content)
        created_samples = []
        created_experiments = []
        created_runs = []
        linked_file_ids = []

        storage = StorageService()

        for i, row in enumerate(rows):
            rv = report.rows[i]

            # 1. Create sample
            sample = await create_sample(self.db, SampleCreate(
                project_accession=project_accession,
                checklist_id=checklist_id,
                organism=row.get("organism", ""),
                tax_id=int(row.get("tax_id", 0)),
                collection_date=row.get("collection_date", ""),
                geographic_location=row.get("geographic_location", ""),
                breed=row.get("breed"),
                host=row.get("host"),
                tissue=row.get("tissue"),
                sex=row.get("sex"),
            ))
            created_samples.append(sample.internal_accession)

            # 2. Create experiment
            platform = row.get("platform", "ILLUMINA")
            library_strategy = row.get("library_strategy", "WGS")
            library_layout = "PAIRED" if rv.reverse_file else "SINGLE"

            experiment = await create_experiment(self.db, ExperimentCreate(
                sample_accession=sample.internal_accession,
                platform=platform,
                instrument_model=row.get("instrument_model", "unspecified"),
                library_strategy=library_strategy,
                library_source=row.get("library_source", "GENOMIC"),
                library_layout=library_layout,
                insert_size=int(row.get("insert_size", 0)) or None,
            ))
            created_experiments.append(experiment.internal_accession)

            # 3. Create runs + move files
            if rv.forward_file:
                archive_path = StorageService.build_object_path(
                    project_accession, sample.internal_accession,
                    f"fwd-{rv.forward_file.staged_file_id}", rv.forward_file.filename,
                )
                run = await create_run(
                    self.db,
                    experiment_accession=experiment.internal_accession,
                    file_type=self._detect_file_type(rv.forward_file.filename),
                    file_path=archive_path,
                    file_size=0,
                    checksum_md5=rv.forward_file.md5,
                )
                created_runs.append(run.internal_accession)
                linked_file_ids.append(rv.forward_file.staged_file_id)

            if rv.reverse_file:
                archive_path = StorageService.build_object_path(
                    project_accession, sample.internal_accession,
                    f"rev-{rv.reverse_file.staged_file_id}", rv.reverse_file.filename,
                )
                run = await create_run(
                    self.db,
                    experiment_accession=experiment.internal_accession,
                    file_type=self._detect_file_type(rv.reverse_file.filename),
                    file_path=archive_path,
                    file_size=0,
                    checksum_md5=rv.reverse_file.md5,
                )
                created_runs.append(run.internal_accession)
                linked_file_ids.append(rv.reverse_file.staged_file_id)

        # Mark staged files as linked
        staging_svc = StagingService(self.db)
        await staging_svc.mark_linked(linked_file_ids)

        return {
            "status": "created",
            "samples": created_samples,
            "experiments": created_experiments,
            "runs": created_runs,
        }

    @staticmethod
    def _detect_file_type(filename: str) -> str:
        lower = filename.lower()
        if lower.endswith((".fastq", ".fastq.gz", ".fq", ".fq.gz")):
            return "FASTQ"
        if lower.endswith(".bam"):
            return "BAM"
        if lower.endswith(".cram"):
            return "CRAM"
        if lower.endswith((".vcf", ".vcf.gz")):
            return "VCF"
        return "OTHER"
```

**Step 4: Run tests**

Run: `cd backend && python -m pytest tests/test_bulk_submit.py -v`
Expected: All 3 tests pass.

**Step 5: Commit**

```bash
git add backend/app/services/bulk_submit.py backend/tests/test_bulk_submit.py
git commit -m "feat: add BulkSubmitService with sample sheet parsing and validation"
```

---

### Task 11: Create Bulk Submit API Endpoints

**Files:**
- Create: `backend/app/api/v1/bulk_submit.py`
- Modify: `backend/app/api/v1/router.py`

**Step 1: Create the endpoints**

```python
# backend/app/api/v1/bulk_submit.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.bulk_submit import BulkSubmitService
from app.services.templates import generate_template_tsv

router = APIRouter(prefix="/bulk-submit", tags=["bulk-submit"])


@router.get("/template/{checklist_id}")
async def download_bulk_template(checklist_id: str):
    """Download a bulk sample sheet template with file linkage columns."""
    tsv = generate_template_tsv(checklist_id)
    if tsv is None:
        raise HTTPException(status_code=404, detail=f"Checklist '{checklist_id}' not found")
    # Add sample_alias as first column and file linkage columns
    lines = tsv.strip().split("\n")
    header = "sample_alias\t" + lines[0] + "\tfilename_forward\tfilename_reverse\tmd5_forward\tmd5_reverse\tlibrary_strategy\tplatform\tinstrument_model"
    example = "SAMPLE01\t" + lines[1] + "\tSAMPLE01_R1.fastq.gz\tSAMPLE01_R2.fastq.gz\t<md5>\t<md5>\tWGS\tILLUMINA\tunspecified"
    content = header + "\n" + example + "\n"

    from fastapi.responses import StreamingResponse
    import io
    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="text/tab-separated-values",
        headers={"Content-Disposition": f'attachment; filename="bulk_{checklist_id}_template.tsv"'},
    )


@router.post("/validate")
async def validate_sample_sheet(
    file: UploadFile = File(...),
    checklist_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = (await file.read()).decode("utf-8")
    svc = BulkSubmitService(db)
    report = await svc.validate_sample_sheet(content, checklist_id, user.id)
    return {
        "valid": report.valid,
        "total_rows": len(report.rows),
        "errors": [e for rv in report.rows for e in rv.errors],
        "warnings": [w for rv in report.rows for w in rv.warnings],
        "rows": [
            {
                "row": rv.row_num,
                "sample_alias": rv.sample_alias,
                "forward_file": rv.forward_file.filename if rv.forward_file else None,
                "reverse_file": rv.reverse_file.filename if rv.reverse_file else None,
                "errors": rv.errors,
            }
            for rv in report.rows
        ],
    }


@router.post("/confirm")
async def confirm_bulk_submit(
    file: UploadFile = File(...),
    project_accession: str = Form(...),
    checklist_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = (await file.read()).decode("utf-8")
    svc = BulkSubmitService(db)

    # Re-validate before creating
    report = await svc.validate_sample_sheet(content, checklist_id, user.id)
    if not report.valid:
        raise HTTPException(status_code=400, detail="Validation failed. Fix errors and try again.")

    result = await svc.confirm_submission(content, project_accession, checklist_id, user.id, report)
    return result
```

**Step 2: Register in router**

Add to `backend/app/api/v1/router.py`:
```python
from app.api.v1.bulk_submit import router as bulk_submit_router
api_router.include_router(bulk_submit_router)
```

**Step 3: Run tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All tests pass.

**Step 4: Commit**

```bash
git add backend/app/api/v1/bulk_submit.py backend/app/api/v1/router.py
git commit -m "feat: add bulk-submit API endpoints (template, validate, confirm)"
```

---

### Task 12: Create FTP Watcher Service

**Files:**
- Create: `backend/app/services/ftp_watcher.py`
- Create: `backend/tests/test_ftp_watcher.py`

**Step 1: Write the test**

```python
# backend/tests/test_ftp_watcher.py
import pytest
import os
import tempfile
from app.services.ftp_watcher import compute_md5, parse_ftp_username


def test_compute_md5():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".fastq") as f:
        f.write(b"@SEQ_ID\nGATTACA\n+\n!!!!!!!!\n")
        f.flush()
        md5 = compute_md5(f.name)
    os.unlink(f.name)
    assert len(md5) == 32
    assert all(c in "0123456789abcdef" for c in md5)


def test_parse_ftp_username():
    user_id = parse_ftp_username("nfdp_user_5")
    assert user_id == 5

    user_id = parse_ftp_username("nfdp_user_123")
    assert user_id == 123

    user_id = parse_ftp_username("invalid")
    assert user_id is None
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_ftp_watcher.py -v`
Expected: ImportError.

**Step 3: Implement**

```python
# backend/app/services/ftp_watcher.py
import hashlib
import os
import asyncio
import logging
from pathlib import Path
from app.services.storage import StorageService
from app.services.staging import BUCKET_STAGING

logger = logging.getLogger(__name__)


def compute_md5(filepath: str) -> str:
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_ftp_username(username: str) -> int | None:
    """Extract user_id from FTP username like 'nfdp_user_5'."""
    if username.startswith("nfdp_user_"):
        try:
            return int(username.split("_")[-1])
        except ValueError:
            return None
    return None


class FTPWatcherService:
    """Watches FTP incoming directory and moves files to MinIO staging."""

    def __init__(self, ftp_base_dir: str = "/data/ftp-incoming"):
        self.ftp_base_dir = Path(ftp_base_dir)
        self.storage = StorageService()
        self.processed_files: set[str] = set()

    async def scan_once(self, db_session_factory) -> list[dict]:
        """Scan all user directories for new files. Returns list of processed files."""
        results = []
        if not self.ftp_base_dir.exists():
            return results

        for user_dir in self.ftp_base_dir.iterdir():
            if not user_dir.is_dir():
                continue

            user_id = parse_ftp_username(user_dir.name)
            if user_id is None:
                continue

            for filepath in user_dir.iterdir():
                if not filepath.is_file():
                    continue
                if str(filepath) in self.processed_files:
                    continue

                try:
                    md5 = compute_md5(str(filepath))
                    staging_path = f"{user_id}/{filepath.name}"

                    # Upload to MinIO staging
                    self.storage.ensure_buckets()
                    self.storage.client.fput_object(
                        BUCKET_STAGING, staging_path, str(filepath)
                    )

                    # Register in database
                    async with db_session_factory() as db:
                        from app.services.staging import StagingService
                        svc = StagingService(db)
                        await svc.register_file(
                            user_id=user_id,
                            filename=filepath.name,
                            file_size=filepath.stat().st_size,
                            checksum_md5=md5,
                            upload_method="ftp",
                            staging_path=staging_path,
                        )

                    # Remove from FTP directory after successful transfer
                    filepath.unlink()
                    self.processed_files.add(str(filepath))
                    results.append({"user_id": user_id, "filename": filepath.name, "md5": md5})
                    logger.info(f"FTP: processed {filepath.name} for user {user_id}")
                except Exception as e:
                    logger.error(f"FTP: failed to process {filepath}: {e}")

        return results

    async def run_forever(self, db_session_factory, interval: int = 30):
        """Poll the FTP directory every `interval` seconds."""
        logger.info(f"FTP Watcher started, monitoring {self.ftp_base_dir}")
        while True:
            try:
                await self.scan_once(db_session_factory)
            except Exception as e:
                logger.error(f"FTP Watcher error: {e}")
            await asyncio.sleep(interval)
```

**Step 4: Run tests**

Run: `cd backend && python -m pytest tests/test_ftp_watcher.py -v`
Expected: Both tests pass.

**Step 5: Commit**

```bash
git add backend/app/services/ftp_watcher.py backend/tests/test_ftp_watcher.py
git commit -m "feat: add FTP watcher service for staging file ingestion"
```

---

### Task 13: Update Frontend — Rename Study → Project

**Files:**
- Modify: `frontend/src/components/wizard/study-step.tsx` → rename to `project-step.tsx`
- Modify: `frontend/src/app/submit/page.tsx`
- Modify: `frontend/src/app/dashboard/page.tsx`
- Modify: `frontend/src/app/browse/page.tsx`
- Modify: `frontend/src/app/fair/page.tsx`
- Modify: `frontend/src/app/admin/ena/page.tsx`

**Step 1: Rename study-step component**

Copy `study-step.tsx` to `project-step.tsx`. Rename:
- `StudyStep` → `ProjectStep`
- `StudyData` → `ProjectData`
- "Study Information" → "Project Information"
- "Study Title" → "Project Title"

**Step 2: Update all pages**

In every page that references `/studies` API endpoint → `/projects`.
In `submit/page.tsx`: import `ProjectStep` instead of `StudyStep`, rename state variable `study` → `project`, `studyAcc` → `projectAcc`.

**Step 3: Build and verify**

Run: `cd frontend && npx next build`
Expected: Build passes with no errors.

**Step 4: Commit**

```bash
git add frontend/src/
git commit -m "refactor: rename Study to Project throughout frontend"
```

---

### Task 14: Frontend — Submit Mode Selector

**Files:**
- Modify: `frontend/src/app/submit/page.tsx`

**Step 1: Create mode selector UI**

Replace the current submit page with a mode selector that shows two cards:

```tsx
"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Upload, FileSpreadsheet } from "lucide-react";
import { QuickSubmit } from "@/components/submit/quick-submit";
import { BulkSubmit } from "@/components/submit/bulk-submit";

export default function SubmitPage() {
  const [mode, setMode] = useState<"select" | "quick" | "bulk">("select");

  if (mode === "quick") return <QuickSubmit onBack={() => setMode("select")} />;
  if (mode === "bulk") return <BulkSubmit onBack={() => setMode("select")} />;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <h2 className="text-3xl font-bold tracking-tight">Submit Data</h2>
      <p className="text-muted-foreground">Choose a submission method</p>
      <div className="grid gap-6 md:grid-cols-2">
        <Card className="cursor-pointer hover:border-primary transition-colors" onClick={() => setMode("quick")}>
          <CardHeader>
            <Upload className="h-8 w-8 text-primary mb-2" />
            <CardTitle>Quick Submit</CardTitle>
            <CardDescription>Single sample with inline file upload. Best for one-off submissions.</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>Create project, sample, experiment</li>
              <li>Upload files directly</li>
              <li>Step-by-step wizard</li>
            </ul>
          </CardContent>
        </Card>
        <Card className="cursor-pointer hover:border-primary transition-colors" onClick={() => setMode("bulk")}>
          <CardHeader>
            <FileSpreadsheet className="h-8 w-8 text-primary mb-2" />
            <CardTitle>Bulk Submit</CardTitle>
            <CardDescription>Multiple samples via sample sheet. ENA-style upload-first workflow.</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>Upload files to staging (or FTP)</li>
              <li>Fill sample sheet with metadata + checksums</li>
              <li>Auto-link files by MD5 validation</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

**Step 2: Move existing wizard to QuickSubmit component**

Create `frontend/src/components/submit/quick-submit.tsx` — move the existing wizard code here, add `onBack` prop.

**Step 3: Create empty BulkSubmit placeholder**

Create `frontend/src/components/submit/bulk-submit.tsx` with a placeholder.

**Step 4: Build and verify**

Run: `cd frontend && npx next build`

**Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: add submit mode selector (Quick Submit vs Bulk Submit)"
```

---

### Task 15: Frontend — Bulk Submit: Project Step

**Files:**
- Modify: `frontend/src/components/submit/bulk-submit.tsx`

**Step 1: Implement project creation/selection step**

The first step of bulk submit lets user create a new project or select an existing one. Use React Query to fetch existing projects from `GET /projects/`.

**Step 2: Build and verify**

**Step 3: Commit**

```bash
git add frontend/src/components/submit/
git commit -m "feat: bulk submit — project step with create/select"
```

---

### Task 16: Frontend — Bulk Submit: File Staging Step

**Files:**
- Create: `frontend/src/components/submit/staging-upload.tsx`
- Modify: `frontend/src/components/submit/bulk-submit.tsx`

**Step 1: Implement staging upload UI**

- Drag-and-drop zone (reuse pattern from upload-step.tsx)
- Files upload to `POST /staging/initiate` → presigned PUT to MinIO
- Browser computes MD5 using Web Crypto API
- After upload completes, update staged file MD5 via API
- Table showing staged files from `GET /staging/files` with name, size, MD5, status
- Delete button per file via `DELETE /staging/files/{id}`
- FTP instructions panel: show connection details and user's FTP directory

**Step 2: Build and verify**

**Step 3: Commit**

```bash
git add frontend/src/components/submit/
git commit -m "feat: bulk submit — file staging step with drag-and-drop and FTP info"
```

---

### Task 17: Frontend — Bulk Submit: Sample Sheet Step

**Files:**
- Create: `frontend/src/components/submit/sample-sheet-step.tsx`
- Modify: `frontend/src/components/submit/bulk-submit.tsx`

**Step 1: Implement sample sheet step**

- Checklist selector dropdown
- "Download Template" button → `GET /bulk-submit/template/{checklist_id}`
- File input for uploading filled TSV
- On upload: `POST /bulk-submit/validate` → display validation report
  - Green banner: "All N rows valid, M files matched"
  - Red banner: row-level errors with field and message
  - Table showing each row: alias, matched files, errors
- "Next" button enabled only when validation passes

**Step 2: Build and verify**

**Step 3: Commit**

```bash
git add frontend/src/components/submit/
git commit -m "feat: bulk submit — sample sheet step with validation report"
```

---

### Task 18: Frontend — Bulk Submit: Confirm Step

**Files:**
- Create: `frontend/src/components/submit/confirm-step.tsx`
- Modify: `frontend/src/components/submit/bulk-submit.tsx`

**Step 1: Implement confirm step**

- Summary table: sample_alias, organism, forward file, reverse file
- "Confirm & Create" button → `POST /bulk-submit/confirm`
- On success: show all created accessions (samples, experiments, runs)
- On error: show error message with option to go back

**Step 2: Build and verify**

Run: `cd frontend && npx next build`

**Step 3: Commit**

```bash
git add frontend/src/components/submit/
git commit -m "feat: bulk submit — confirm step with entity creation"
```

---

### Task 19: Add MinIO Staging Bucket to Storage Service

**Files:**
- Modify: `backend/app/services/storage.py`

**Step 1: Add BUCKET_STAGING constant**

Add `BUCKET_STAGING = "nfdp-staging"` to StorageService and include it in `ensure_buckets()`.

**Step 2: Add MD5 computation for staged files**

Add a method `compute_object_md5(bucket, path)` that downloads the object and computes MD5, used after browser uploads to verify integrity.

**Step 3: Run tests**

**Step 4: Commit**

```bash
git add backend/app/services/storage.py
git commit -m "feat: add staging bucket and MD5 computation to StorageService"
```

---

### Task 20: Update Staging API to Compute MD5 After Upload

**Files:**
- Create: `backend/app/api/v1/staging.py` (add complete endpoint)

**Step 1: Add POST /staging/complete endpoint**

After browser upload, client calls this to trigger server-side MD5 computation:

```python
@router.post("/complete/{staged_file_id}")
async def complete_staging_upload(
    staged_file_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Fetch staged file record
    # Compute MD5 of the object in MinIO
    # Update the staged_file.checksum_md5 and status=verified
    # Return updated record
```

**Step 2: Run tests**

**Step 3: Commit**

```bash
git add backend/app/api/v1/staging.py
git commit -m "feat: add staging complete endpoint for server-side MD5 computation"
```

---

### Task 21: Integration Test — Full Bulk Submit Flow

**Files:**
- Create: `backend/tests/test_bulk_submit_integration.py`

**Step 1: Write end-to-end test**

```python
@pytest.mark.asyncio
async def test_full_bulk_submit_flow(client, auth_headers):
    # 1. Create project
    r = await client.post("/api/v1/projects/", json={...}, headers=auth_headers)
    project_acc = r.json()["accession"]

    # 2. Stage files (simulate by inserting staged_file records)
    # 3. Upload sample sheet to /bulk-submit/validate
    # 4. Assert validation passes
    # 5. Confirm via /bulk-submit/confirm
    # 6. Assert samples, experiments, runs created
    # 7. Assert staged files marked as linked
```

**Step 2: Run test**

Run: `cd backend && python -m pytest tests/test_bulk_submit_integration.py -v`
Expected: Test passes.

**Step 3: Commit**

```bash
git add backend/tests/test_bulk_submit_integration.py
git commit -m "test: add end-to-end integration test for bulk submit flow"
```

---

### Task 22: Final Verification and Cleanup

**Step 1: Run all backend tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All tests pass.

**Step 2: Build frontend**

Run: `cd frontend && npx next build`
Expected: Build passes.

**Step 3: Manual smoke test**

1. Start backend + frontend + MinIO
2. Login
3. Test Quick Submit flow (should still work)
4. Test Bulk Submit flow:
   - Create project
   - Upload files to staging
   - Download template, fill, upload
   - Validate
   - Confirm
   - Verify accessions

**Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final cleanup for ENA-style bulk submit feature"
```
