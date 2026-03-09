# NFDP Genomic Deposition System — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a genomic data deposition system (internal archive + ENA public submission) for a livestock/pathogen sequencing facility.

**Architecture:** Next.js frontend + FastAPI backend + PostgreSQL metadata DB + MinIO object storage + Redis job queue + Nextflow pipelines. Everything runs locally via Docker Compose during development.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, MinIO (boto3/minio-py), Redis (arq), Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, Docker Compose, pytest, Vitest.

**Reference:** `docs/plans/2026-03-06-genomic-deposition-system-blueprint.md`

---

## Phase 1: Project Scaffolding & Infrastructure

### Task 1: Initialize monorepo structure

**Files:**
- Create: `docker-compose.yml`
- Create: `backend/pyproject.toml`
- Create: `backend/Dockerfile`
- Create: `frontend/package.json`
- Create: `frontend/Dockerfile`
- Create: `.env.example`
- Create: `.gitignore`

**Step 1: Create directory structure**

```bash
mkdir -p backend/app/{api,models,schemas,services,workers,plugins}
mkdir -p backend/app/api/v1
mkdir -p backend/app/plugins/{checklists,qc_handlers,exporters,integrations}
mkdir -p backend/tests
mkdir -p frontend
mkdir -p pipelines
```

**Step 2: Create backend pyproject.toml**

```toml
[project]
name = "nfdp-genomics"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "minio>=7.2.0",
    "redis>=5.0.0",
    "arq>=0.26.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.18",
    "jsonschema>=4.23.0",
    "httpx>=0.28.0",
    "emails>=0.6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "httpx>=0.28.0",
    "factory-boy>=3.3.0",
    "ruff>=0.8.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
target-version = "py312"
line-length = 100
```

**Step 3: Create .env.example**

```env
# Database
DATABASE_URL=postgresql+asyncpg://nfdp:nfdp@localhost:5432/nfdp

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# App
APP_ENV=development
APP_DEBUG=true
```

**Step 4: Create docker-compose.yml**

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: nfdp
      POSTGRES_USER: nfdp
      POSTGRES_PASSWORD: nfdp
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - miniodata:/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - minio
      - redis

  worker:
    build: ./backend
    command: arq app.workers.main.WorkerSettings
    env_file: .env
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - minio
      - redis

  frontend:
    build: ./frontend
    command: npm run dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend

volumes:
  pgdata:
  miniodata:
```

**Step 5: Create backend Dockerfile**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install -e ".[dev]"
COPY . .
```

**Step 6: Create .gitignore**

```gitignore
__pycache__/
*.pyc
.env
.venv/
node_modules/
.next/
*.egg-info/
dist/
.pytest_cache/
.coverage
htmlcov/
```

**Step 7: Commit**

```bash
git add -A
git commit -m "feat: initialize monorepo with Docker Compose infrastructure"
```

---

### Task 2: FastAPI application skeleton with health check

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/v1/__init__.py`
- Create: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_health.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_health.py
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_health.py -v`
Expected: FAIL (ImportError — app.main does not exist yet)

**Step 3: Write config.py**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://nfdp:nfdp@localhost:5432/nfdp"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    app_env: str = "development"
    app_debug: bool = True

    model_config = {"env_file": ".env"}


settings = Settings()
```

**Step 4: Write database.py**

```python
# backend/app/database.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=settings.app_debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session
```

**Step 5: Write main.py with health endpoint**

```python
# backend/app/main.py
from fastapi import FastAPI
from app.api.v1.router import api_router

app = FastAPI(title="NFDP Genomic Deposition System", version="0.1.0")
app.include_router(api_router, prefix="/api/v1")
```

```python
# backend/app/api/__init__.py
# backend/app/api/v1/__init__.py
# (empty init files)
```

```python
# backend/app/api/v1/router.py
from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}
```

**Step 6: Create empty __init__.py files**

```bash
touch backend/app/__init__.py backend/app/api/__init__.py backend/app/api/v1/__init__.py
touch backend/app/models/__init__.py backend/app/schemas/__init__.py
touch backend/app/services/__init__.py backend/app/workers/__init__.py
touch backend/app/plugins/__init__.py backend/tests/__init__.py
```

**Step 7: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_health.py -v`
Expected: PASS

**Step 8: Commit**

```bash
git add backend/
git commit -m "feat: add FastAPI skeleton with health check endpoint"
```

---

## Phase 2: Data Model & Database

### Task 3: Accession generator utility

**Files:**
- Create: `backend/app/services/accession.py`
- Test: `backend/tests/test_accession.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_accession.py
import pytest
from app.services.accession import generate_accession, validate_accession, AccessionType


def test_generate_accession_study():
    acc = generate_accession(AccessionType.STUDY, 1)
    assert acc == "NFDP-PRJ-000001"


def test_generate_accession_sample():
    acc = generate_accession(AccessionType.SAMPLE, 42)
    assert acc == "NFDP-SAM-000042"


def test_generate_accession_experiment():
    acc = generate_accession(AccessionType.EXPERIMENT, 100)
    assert acc == "NFDP-EXP-000100"


def test_generate_accession_run():
    acc = generate_accession(AccessionType.RUN, 999999)
    assert acc == "NFDP-RUN-999999"


def test_generate_accession_submission():
    acc = generate_accession(AccessionType.SUBMISSION, 15)
    assert acc == "NFDP-SUB-000015"


def test_validate_accession_valid():
    assert validate_accession("NFDP-PRJ-000001") is True
    assert validate_accession("NFDP-SAM-123456") is True


def test_validate_accession_invalid():
    assert validate_accession("INVALID") is False
    assert validate_accession("NFDP-XXX-000001") is False
    assert validate_accession("NFDP-PRJ-1") is False
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_accession.py -v`
Expected: FAIL (ImportError)

**Step 3: Write minimal implementation**

```python
# backend/app/services/accession.py
import re
from enum import Enum


class AccessionType(str, Enum):
    STUDY = "PRJ"
    SAMPLE = "SAM"
    EXPERIMENT = "EXP"
    RUN = "RUN"
    SUBMISSION = "SUB"


_ACCESSION_PATTERN = re.compile(r"^NFDP-(PRJ|SAM|EXP|RUN|SUB)-\d{6}$")


def generate_accession(acc_type: AccessionType, sequence: int) -> str:
    return f"NFDP-{acc_type.value}-{sequence:06d}"


def validate_accession(accession: str) -> bool:
    return bool(_ACCESSION_PATTERN.match(accession))
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_accession.py -v`
Expected: PASS (7 passed)

**Step 5: Commit**

```bash
git add backend/app/services/accession.py backend/tests/test_accession.py
git commit -m "feat: add accession generator and validator (NFDP-{TYPE}-{SEQ})"
```

---

### Task 4: SQLAlchemy models for core entities

**Files:**
- Create: `backend/app/models/enums.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/study.py`
- Create: `backend/app/models/sample.py`
- Create: `backend/app/models/experiment.py`
- Create: `backend/app/models/run.py`
- Create: `backend/app/models/submission.py`
- Create: `backend/app/models/qc_report.py`
- Modify: `backend/app/models/__init__.py`
- Test: `backend/tests/test_models.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_models.py
from app.models.enums import (
    Platform, LibraryStrategy, LibrarySource, LibraryLayout,
    FileType, ProjectType, SubmissionStatus, QCStatus, UserRole,
)
from app.models.study import Study
from app.models.sample import Sample
from app.models.experiment import Experiment
from app.models.run import Run
from app.models.submission import Submission
from app.models.user import User
from app.models.qc_report import QCReport


def test_enums_exist():
    assert Platform.ILLUMINA.value == "ILLUMINA"
    assert Platform.OXFORD_NANOPORE.value == "OXFORD_NANOPORE"
    assert Platform.PACBIO_SMRT.value == "PACBIO_SMRT"
    assert Platform.SNP_CHIP.value == "SNP_CHIP"
    assert Platform.HI_C.value == "HI_C"
    assert FileType.FASTQ.value == "FASTQ"
    assert SubmissionStatus.DRAFT.value == "draft"
    assert UserRole.ADMIN.value == "admin"


def test_study_table_name():
    assert Study.__tablename__ == "studies"


def test_sample_table_name():
    assert Sample.__tablename__ == "samples"


def test_experiment_table_name():
    assert Experiment.__tablename__ == "experiments"


def test_run_table_name():
    assert Run.__tablename__ == "runs"


def test_submission_table_name():
    assert Submission.__tablename__ == "submissions"


def test_user_table_name():
    assert User.__tablename__ == "users"


def test_qc_report_table_name():
    assert QCReport.__tablename__ == "qc_reports"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_models.py -v`
Expected: FAIL (ImportError)

**Step 3: Write enums**

```python
# backend/app/models/enums.py
import enum


class Platform(str, enum.Enum):
    ILLUMINA = "ILLUMINA"
    OXFORD_NANOPORE = "OXFORD_NANOPORE"
    PACBIO_SMRT = "PACBIO_SMRT"
    SNP_CHIP = "SNP_CHIP"
    HI_C = "HI_C"


class LibraryStrategy(str, enum.Enum):
    WGS = "WGS"
    WXS = "WXS"
    RNA_SEQ = "RNA-Seq"
    AMPLICON = "AMPLICON"
    TARGETED = "TARGETED"
    OTHER = "OTHER"


class LibrarySource(str, enum.Enum):
    GENOMIC = "GENOMIC"
    TRANSCRIPTOMIC = "TRANSCRIPTOMIC"
    METAGENOMIC = "METAGENOMIC"
    OTHER = "OTHER"


class LibraryLayout(str, enum.Enum):
    PAIRED = "PAIRED"
    SINGLE = "SINGLE"


class FileType(str, enum.Enum):
    FASTQ = "FASTQ"
    BAM = "BAM"
    CRAM = "CRAM"
    VCF = "VCF"
    IDAT = "IDAT"
    BED_BIM_FAM = "BED_BIM_FAM"
    PED_MAP = "PED_MAP"
    CSV = "CSV"
    OTHER = "OTHER"


class ProjectType(str, enum.Enum):
    WGS = "WGS"
    METAGENOMICS = "Metagenomics"
    GENOTYPING = "Genotyping"
    TRANSCRIPTOMICS = "Transcriptomics"
    AMPLICON = "Amplicon"
    OTHER = "Other"


class SubmissionStatus(str, enum.Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    DEPOSITED = "deposited"
    PUBLISHED = "published"
    FAILED = "failed"


class QCStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SUBMITTER = "submitter"
    VIEWER = "viewer"
    EXTERNAL_CLIENT = "external_client"
```

**Step 4: Write User model**

```python
# backend/app/models/user.py
from datetime import datetime
from sqlalchemy import String, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.SUBMITTER)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    studies = relationship("Study", back_populates="created_by_user")
```

**Step 5: Write Study model**

```python
# backend/app/models/study.py
from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, Enum as SAEnum, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ProjectType


class Study(Base):
    __tablename__ = "studies"

    id: Mapped[int] = mapped_column(primary_key=True)
    internal_accession: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    ena_accession: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    project_type: Mapped[ProjectType] = mapped_column(SAEnum(ProjectType))
    release_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    license: Mapped[str] = mapped_column(String(20), default="CC-BY")
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by_user = relationship("User", back_populates="studies")
    samples = relationship("Sample", back_populates="study")
```

**Step 6: Write Sample model**

```python
# backend/app/models/sample.py
from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Date, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Sample(Base):
    __tablename__ = "samples"

    id: Mapped[int] = mapped_column(primary_key=True)
    internal_accession: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    ena_accession: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    organism: Mapped[str] = mapped_column(String(255))
    tax_id: Mapped[int] = mapped_column(Integer)
    breed: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    collection_date: Mapped[date] = mapped_column(Date)
    geographic_location: Mapped[str] = mapped_column(String(255))
    host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tissue: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    developmental_stage: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sex: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    checklist_id: Mapped[str] = mapped_column(String(20))
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("studies.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    study = relationship("Study", back_populates="samples")
    experiments = relationship("Experiment", back_populates="sample")
```

**Step 7: Write Experiment model**

```python
# backend/app/models/experiment.py
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import Platform, LibraryStrategy, LibrarySource, LibraryLayout


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    internal_accession: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    ena_accession: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    platform: Mapped[Platform] = mapped_column(SAEnum(Platform))
    instrument_model: Mapped[str] = mapped_column(String(255))
    library_strategy: Mapped[LibraryStrategy] = mapped_column(SAEnum(LibraryStrategy))
    library_source: Mapped[LibrarySource] = mapped_column(SAEnum(LibrarySource))
    library_layout: Mapped[LibraryLayout] = mapped_column(SAEnum(LibraryLayout))
    insert_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sample_id: Mapped[int] = mapped_column(ForeignKey("samples.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    sample = relationship("Sample", back_populates="experiments")
    runs = relationship("Run", back_populates="experiment")
```

**Step 8: Write Run model**

```python
# backend/app/models/run.py
from datetime import datetime
from typing import Optional
from sqlalchemy import String, BigInteger, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import FileType


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    internal_accession: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    ena_accession: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    file_type: Mapped[FileType] = mapped_column(SAEnum(FileType))
    file_path: Mapped[str] = mapped_column(String(1000))
    file_size: Mapped[int] = mapped_column(BigInteger)
    checksum_md5: Mapped[str] = mapped_column(String(32))
    checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="runs")
    qc_reports = relationship("QCReport", back_populates="run")
```

**Step 9: Write Submission model**

```python
# backend/app/models/submission.py
from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import SubmissionStatus


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    internal_accession: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    status: Mapped[SubmissionStatus] = mapped_column(
        SAEnum(SubmissionStatus), default=SubmissionStatus.DRAFT
    )
    study_id: Mapped[int] = mapped_column(ForeignKey("studies.id"))
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    run_accessions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    validation_report: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Step 10: Write QCReport model**

```python
# backend/app/models/qc_report.py
from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import QCStatus


class QCReport(Base):
    __tablename__ = "qc_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    status: Mapped[QCStatus] = mapped_column(SAEnum(QCStatus), default=QCStatus.PENDING)
    tool: Mapped[str] = mapped_column(String(100))
    summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    report_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    run = relationship("Run", back_populates="qc_reports")
```

**Step 11: Update models __init__.py**

```python
# backend/app/models/__init__.py
from app.models.user import User
from app.models.study import Study
from app.models.sample import Sample
from app.models.experiment import Experiment
from app.models.run import Run
from app.models.submission import Submission
from app.models.qc_report import QCReport
from app.models.enums import (
    Platform, LibraryStrategy, LibrarySource, LibraryLayout,
    FileType, ProjectType, SubmissionStatus, QCStatus, UserRole,
)

__all__ = [
    "User", "Study", "Sample", "Experiment", "Run", "Submission", "QCReport",
    "Platform", "LibraryStrategy", "LibrarySource", "LibraryLayout",
    "FileType", "ProjectType", "SubmissionStatus", "QCStatus", "UserRole",
]
```

**Step 12: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_models.py -v`
Expected: PASS (8 passed)

**Step 13: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add SQLAlchemy models for all core ENA/INSDC entities"
```

---

### Task 5: Alembic migrations setup

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/` (auto-generated)

**Step 1: Initialize Alembic**

```bash
cd backend && alembic init alembic
```

**Step 2: Edit alembic/env.py to use async and import models**

Replace the generated `env.py` with:

```python
# backend/alembic/env.py
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.config import settings
from app.database import Base
from app.models import *  # noqa: F401,F403 — import all models for autogenerate

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=settings.database_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online():
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 3: Generate initial migration**

```bash
cd backend && alembic revision --autogenerate -m "initial schema"
```

**Step 4: Apply migration (requires running PostgreSQL)**

```bash
docker compose up -d postgres
sleep 3
cd backend && alembic upgrade head
```

**Step 5: Commit**

```bash
git add backend/alembic/ backend/alembic.ini
git commit -m "feat: add Alembic migrations with initial schema"
```

---

## Phase 3: Pydantic Schemas & Auth

### Task 6: Pydantic schemas for all entities

**Files:**
- Create: `backend/app/schemas/user.py`
- Create: `backend/app/schemas/study.py`
- Create: `backend/app/schemas/sample.py`
- Create: `backend/app/schemas/experiment.py`
- Create: `backend/app/schemas/run.py`
- Create: `backend/app/schemas/submission.py`
- Test: `backend/tests/test_schemas.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_schemas.py
import pytest
from datetime import date
from pydantic import ValidationError
from app.schemas.study import StudyCreate, StudyResponse
from app.schemas.sample import SampleCreate


def test_study_create_valid():
    s = StudyCreate(
        title="Camel WGS",
        description="WGS of dromedary camels",
        project_type="WGS",
    )
    assert s.title == "Camel WGS"


def test_study_create_missing_required():
    with pytest.raises(ValidationError):
        StudyCreate(title="No description")


def test_sample_create_valid():
    s = SampleCreate(
        study_accession="NFDP-PRJ-000001",
        checklist_id="ERC000055",
        organism="Camelus dromedarius",
        tax_id=9838,
        collection_date=date(2026, 1, 15),
        geographic_location="Saudi Arabia:Riyadh",
    )
    assert s.tax_id == 9838


def test_sample_create_invalid_accession():
    with pytest.raises(ValidationError):
        SampleCreate(
            study_accession="INVALID",
            checklist_id="ERC000055",
            organism="Camelus dromedarius",
            tax_id=9838,
            collection_date=date(2026, 1, 15),
            geographic_location="Saudi Arabia:Riyadh",
        )
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_schemas.py -v`
Expected: FAIL

**Step 3: Write schemas**

```python
# backend/app/schemas/study.py
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from app.models.enums import ProjectType


class StudyCreate(BaseModel):
    title: str
    description: str
    project_type: ProjectType
    release_date: Optional[date] = None
    license: str = "CC-BY"


class StudyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    release_date: Optional[date] = None
    license: Optional[str] = None


class StudyResponse(BaseModel):
    accession: str
    ena_accession: Optional[str] = None
    title: str
    description: str
    project_type: ProjectType
    release_date: Optional[date] = None
    license: str
    created_at: datetime

    model_config = {"from_attributes": True}
```

```python
# backend/app/schemas/sample.py
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, field_validator
from app.services.accession import validate_accession


class SampleCreate(BaseModel):
    study_accession: str
    checklist_id: str
    organism: str
    tax_id: int
    collection_date: date
    geographic_location: str
    breed: Optional[str] = None
    host: Optional[str] = None
    tissue: Optional[str] = None
    developmental_stage: Optional[str] = None
    sex: Optional[str] = None
    custom_fields: Optional[dict] = None

    @field_validator("study_accession")
    @classmethod
    def validate_study_accession(cls, v):
        if not validate_accession(v):
            raise ValueError(f"Invalid accession format: {v}")
        return v


class SampleResponse(BaseModel):
    accession: str
    ena_accession: Optional[str] = None
    organism: str
    tax_id: int
    breed: Optional[str] = None
    collection_date: date
    geographic_location: str
    checklist_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
```

```python
# backend/app/schemas/experiment.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator
from app.models.enums import Platform, LibraryStrategy, LibrarySource, LibraryLayout
from app.services.accession import validate_accession


class ExperimentCreate(BaseModel):
    sample_accession: str
    platform: Platform
    instrument_model: str
    library_strategy: LibraryStrategy
    library_source: LibrarySource
    library_layout: LibraryLayout
    insert_size: Optional[int] = None

    @field_validator("sample_accession")
    @classmethod
    def validate_sample_accession(cls, v):
        if not validate_accession(v):
            raise ValueError(f"Invalid accession format: {v}")
        return v


class ExperimentResponse(BaseModel):
    accession: str
    ena_accession: Optional[str] = None
    platform: Platform
    instrument_model: str
    library_strategy: LibraryStrategy
    library_source: LibrarySource
    library_layout: LibraryLayout
    insert_size: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}
```

```python
# backend/app/schemas/run.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.enums import FileType


class RunResponse(BaseModel):
    accession: str
    ena_accession: Optional[str] = None
    file_type: FileType
    file_size: int
    checksum_md5: str
    created_at: datetime

    model_config = {"from_attributes": True}
```

```python
# backend/app/schemas/submission.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.enums import SubmissionStatus


class SubmissionCreate(BaseModel):
    title: str
    study_accession: str
    run_accessions: list[str]


class SubmissionResponse(BaseModel):
    submission_id: str
    title: str
    status: SubmissionStatus
    created_at: datetime

    model_config = {"from_attributes": True}
```

```python
# backend/app/schemas/user.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.enums import UserRole


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: UserRole = UserRole.SUBMITTER


class UserResponse(BaseModel):
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_schemas.py -v`
Expected: PASS (4 passed)

**Step 5: Commit**

```bash
git add backend/app/schemas/ backend/tests/test_schemas.py
git commit -m "feat: add Pydantic v2 schemas for all entities with validation"
```

---

### Task 7: JWT authentication service

**Files:**
- Create: `backend/app/services/auth.py`
- Create: `backend/app/api/v1/deps.py`
- Create: `backend/app/api/v1/auth.py`
- Test: `backend/tests/test_auth.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_auth.py
import pytest
from app.services.auth import hash_password, verify_password, create_access_token, decode_token


def test_hash_and_verify_password():
    hashed = hash_password("mysecret")
    assert verify_password("mysecret", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_token():
    token = create_access_token(data={"sub": "user@test.com", "role": "admin"})
    payload = decode_token(token)
    assert payload["sub"] == "user@test.com"
    assert payload["role"] == "admin"


def test_decode_invalid_token():
    payload = decode_token("invalid.token.here")
    assert payload is None
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_auth.py -v`
Expected: FAIL

**Step 3: Write auth service**

```python
# backend/app/services/auth.py
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_auth.py -v`
Expected: PASS (3 passed)

**Step 5: Write auth dependency and routes**

```python
# backend/app/api/v1/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.services.auth import decode_token
from app.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
```

```python
# backend/app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, TokenResponse
from app.services.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(email: str, password: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.email, "role": user.role.value})
    refresh_token = create_access_token(data={"sub": user.email, "type": "refresh"})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, expires_in=3600)
```

**Step 6: Register auth router in main router**

Add to `backend/app/api/v1/router.py`:

```python
from app.api.v1.auth import router as auth_router
api_router.include_router(auth_router)
```

**Step 7: Commit**

```bash
git add backend/app/services/auth.py backend/app/api/v1/deps.py backend/app/api/v1/auth.py backend/tests/test_auth.py backend/app/api/v1/router.py
git commit -m "feat: add JWT authentication with register/login endpoints"
```

---

## Phase 4: CRUD API Endpoints

### Task 8: Studies CRUD API

**Files:**
- Create: `backend/app/api/v1/studies.py`
- Create: `backend/app/services/studies.py`
- Test: `backend/tests/test_studies_api.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_studies_api.py
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_create_study_unauthorized():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/studies", json={
            "title": "Test Study",
            "description": "A test",
            "project_type": "WGS",
        })
    assert response.status_code == 403  # No auth token
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_studies_api.py -v`
Expected: FAIL (404 — route doesn't exist)

**Step 3: Write studies service**

```python
# backend/app/services/studies.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.study import Study
from app.models.user import User
from app.schemas.study import StudyCreate, StudyUpdate
from app.services.accession import generate_accession, AccessionType


async def create_study(db: AsyncSession, study_in: StudyCreate, user: User) -> Study:
    result = await db.execute(select(func.count()).select_from(Study))
    count = result.scalar() + 1
    study = Study(
        internal_accession=generate_accession(AccessionType.STUDY, count),
        title=study_in.title,
        description=study_in.description,
        project_type=study_in.project_type,
        release_date=study_in.release_date,
        license=study_in.license,
        created_by_id=user.id,
    )
    db.add(study)
    await db.commit()
    await db.refresh(study)
    return study


async def get_study_by_accession(db: AsyncSession, accession: str) -> Study | None:
    result = await db.execute(select(Study).where(Study.internal_accession == accession))
    return result.scalar_one_or_none()


async def list_studies(db: AsyncSession, page: int = 1, per_page: int = 20) -> list[Study]:
    offset = (page - 1) * per_page
    result = await db.execute(select(Study).offset(offset).limit(per_page).order_by(Study.created_at.desc()))
    return list(result.scalars().all())
```

**Step 4: Write studies router**

```python
# backend/app/api/v1/studies.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.schemas.study import StudyCreate, StudyResponse, StudyUpdate
from app.services.studies import create_study, get_study_by_accession, list_studies

router = APIRouter(prefix="/studies", tags=["studies"])


@router.post("/", response_model=StudyResponse, status_code=201)
async def create(
    study_in: StudyCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    study = await create_study(db, study_in, user)
    return StudyResponse(accession=study.internal_accession, **{
        k: getattr(study, k) for k in ["ena_accession", "title", "description", "project_type", "release_date", "license", "created_at"]
    })


@router.get("/", response_model=list[StudyResponse])
async def list_all(page: int = 1, per_page: int = 20, db: AsyncSession = Depends(get_db)):
    studies = await list_studies(db, page, per_page)
    return [StudyResponse(accession=s.internal_accession, **{
        k: getattr(s, k) for k in ["ena_accession", "title", "description", "project_type", "release_date", "license", "created_at"]
    }) for s in studies]


@router.get("/{accession}", response_model=StudyResponse)
async def get(accession: str, db: AsyncSession = Depends(get_db)):
    study = await get_study_by_accession(db, accession)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return StudyResponse(accession=study.internal_accession, **{
        k: getattr(study, k) for k in ["ena_accession", "title", "description", "project_type", "release_date", "license", "created_at"]
    })
```

**Step 5: Register router**

Add to `backend/app/api/v1/router.py`:

```python
from app.api.v1.studies import router as studies_router
api_router.include_router(studies_router)
```

**Step 6: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_studies_api.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add backend/app/api/v1/studies.py backend/app/services/studies.py backend/tests/test_studies_api.py backend/app/api/v1/router.py
git commit -m "feat: add Studies CRUD API with auth protection"
```

---

### Task 9: Samples CRUD API (including bulk CSV/TSV upload)

Follow same pattern as Task 8. Key differences:

**Files:**
- Create: `backend/app/api/v1/samples.py`
- Create: `backend/app/services/samples.py`
- Test: `backend/tests/test_samples_api.py`

The samples service must:
- Resolve `study_accession` to `study_id`
- Generate `NFDP-SAM-XXXXXX` accessions
- Support `POST /samples/bulk` accepting TSV file upload
- Validate against `checklist_id` (basic validation initially — full checklist in Task 14)
- Store `custom_fields` as JSON

**Step 1-7: Same TDD cycle as Task 8**

**Commit message:** `feat: add Samples CRUD API with bulk TSV upload`

---

### Task 10: Experiments CRUD API

Follow same pattern. Resolve `sample_accession` to `sample_id`.

**Files:**
- Create: `backend/app/api/v1/experiments.py`
- Create: `backend/app/services/experiments.py`
- Test: `backend/tests/test_experiments_api.py`

**Commit message:** `feat: add Experiments CRUD API`

---

### Task 11: Runs CRUD API

Follow same pattern. Resolve `experiment_accession` to `experiment_id`. Include QC report retrieval.

**Files:**
- Create: `backend/app/api/v1/runs.py`
- Create: `backend/app/services/runs.py`
- Test: `backend/tests/test_runs_api.py`

**Commit message:** `feat: add Runs CRUD API with QC report endpoint`

---

## Phase 5: MinIO Storage & File Upload

### Task 12: MinIO service and bucket initialization

**Files:**
- Create: `backend/app/services/storage.py`
- Test: `backend/tests/test_storage.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_storage.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.storage import StorageService


def test_bucket_names():
    assert StorageService.BUCKET_RAW == "nfdp-raw"
    assert StorageService.BUCKET_QC == "nfdp-qc"
    assert StorageService.BUCKET_PROCESSED == "nfdp-processed"
    assert StorageService.BUCKET_SNPCHIP == "nfdp-snpchip"


def test_build_object_path():
    path = StorageService.build_object_path("NFDP-PRJ-000001", "NFDP-SAM-000001", "NFDP-RUN-000001", "sample_R1.fastq.gz")
    assert path == "NFDP-PRJ-000001/NFDP-SAM-000001/NFDP-RUN-000001/sample_R1.fastq.gz"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_storage.py -v`
Expected: FAIL

**Step 3: Write storage service**

```python
# backend/app/services/storage.py
from minio import Minio
from app.config import settings


class StorageService:
    BUCKET_RAW = "nfdp-raw"
    BUCKET_QC = "nfdp-qc"
    BUCKET_PROCESSED = "nfdp-processed"
    BUCKET_SNPCHIP = "nfdp-snpchip"

    ALL_BUCKETS = [BUCKET_RAW, BUCKET_QC, BUCKET_PROCESSED, BUCKET_SNPCHIP]

    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    def ensure_buckets(self):
        for bucket in self.ALL_BUCKETS:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)

    @staticmethod
    def build_object_path(study_acc: str, sample_acc: str, run_acc: str, filename: str) -> str:
        return f"{study_acc}/{sample_acc}/{run_acc}/{filename}"

    def generate_presigned_upload_url(self, bucket: str, object_path: str, expires_hours: int = 24) -> str:
        from datetime import timedelta
        return self.client.presigned_put_object(bucket, object_path, expires=timedelta(hours=expires_hours))

    def generate_presigned_download_url(self, bucket: str, object_path: str, expires_hours: int = 24) -> str:
        from datetime import timedelta
        return self.client.presigned_get_object(bucket, object_path, expires=timedelta(hours=expires_hours))

    def get_object_stat(self, bucket: str, object_path: str):
        return self.client.stat_object(bucket, object_path)


storage_service = StorageService()
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_storage.py -v`
Expected: PASS (2 passed)

**Step 5: Commit**

```bash
git add backend/app/services/storage.py backend/tests/test_storage.py
git commit -m "feat: add MinIO storage service with bucket management and presigned URLs"
```

---

### Task 13: Upload API (initiate, direct upload, complete)

**Files:**
- Create: `backend/app/api/v1/upload.py`
- Create: `backend/app/schemas/upload.py`
- Test: `backend/tests/test_upload_api.py`

**Step 1: Write schemas**

```python
# backend/app/schemas/upload.py
from pydantic import BaseModel
from app.models.enums import FileType


class UploadInitiate(BaseModel):
    experiment_accession: str
    filename: str
    file_size: int
    checksum_md5: str
    file_type: FileType


class UploadInitiateResponse(BaseModel):
    upload_id: str
    presigned_url: str
    expires_in: int


class UploadComplete(BaseModel):
    upload_id: str
    checksum_md5: str


class UploadCompleteResponse(BaseModel):
    run_accession: str
    qc_job_id: str
    status: str
```

**Step 2: Write upload router**

The upload router must:
1. `POST /upload/initiate` — validate experiment exists, generate upload_id (UUID), store in Redis with metadata, return presigned MinIO URL
2. `POST /upload/complete` — retrieve upload metadata from Redis, verify checksum matches, create Run record in DB, queue QC job, return Run accession

**Step 3: Write failing tests, implement, pass, commit**

**Commit message:** `feat: add presigned upload flow (initiate/complete) with checksum verification`

---

## Phase 6: Metadata Validation & Checklists

### Task 14: Checklist-based metadata validation

**Files:**
- Create: `backend/app/plugins/checklists/ERC000011.json`
- Create: `backend/app/plugins/checklists/ERC000055.json`
- Create: `backend/app/plugins/checklists/snpchip_livestock.json`
- Create: `backend/app/services/validation.py`
- Test: `backend/tests/test_validation.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_validation.py
import pytest
from app.services.validation import validate_sample_metadata


def test_validate_farm_animal_valid():
    errors = validate_sample_metadata("ERC000055", {
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "collection_date": "2026-01-15",
        "geographic_location": "Saudi Arabia:Riyadh",
    })
    assert errors == []


def test_validate_farm_animal_missing_required():
    errors = validate_sample_metadata("ERC000055", {
        "organism": "Camelus dromedarius",
    })
    assert len(errors) > 0
    assert any("tax_id" in e["field"] for e in errors)


def test_validate_unknown_checklist():
    errors = validate_sample_metadata("UNKNOWN", {"organism": "test"})
    assert any("checklist" in e["message"].lower() for e in errors)
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_validation.py -v`
Expected: FAIL

**Step 3: Write ERC000055 checklist JSON schema**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ERC000055 - Farm Animal",
  "type": "object",
  "required": ["organism", "tax_id", "collection_date", "geographic_location"],
  "properties": {
    "organism": { "type": "string" },
    "tax_id": { "type": "integer" },
    "collection_date": { "type": "string", "format": "date" },
    "geographic_location": { "type": "string", "pattern": "^.+:.+$" },
    "breed": { "type": "string" },
    "sex": { "type": "string", "enum": ["male", "female", "unknown"] },
    "tissue": { "type": "string" },
    "developmental_stage": { "type": "string" },
    "host": { "type": "string" }
  }
}
```

**Step 4: Write validation service**

```python
# backend/app/services/validation.py
import json
from pathlib import Path
from jsonschema import validate, ValidationError

CHECKLISTS_DIR = Path(__file__).parent.parent / "plugins" / "checklists"


def load_checklist(checklist_id: str) -> dict | None:
    path = CHECKLISTS_DIR / f"{checklist_id}.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def validate_sample_metadata(checklist_id: str, metadata: dict) -> list[dict]:
    schema = load_checklist(checklist_id)
    if schema is None:
        return [{"field": "checklist_id", "message": f"Checklist '{checklist_id}' not found"}]

    errors = []
    try:
        validate(instance=metadata, schema=schema)
    except ValidationError as e:
        # Collect all errors
        from jsonschema import Draft202012Validator
        validator = Draft202012Validator(schema)
        for error in validator.iter_errors(metadata):
            field = ".".join(str(p) for p in error.absolute_path) or error.validator
            errors.append({"field": field, "message": error.message})
    return errors
```

**Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_validation.py -v`
Expected: PASS (3 passed)

**Step 6: Create remaining checklist schemas**

Create `ERC000011.json`, `ERC000020.json`, `ERC000028.json`, `ERC000043.json`, `snpchip_livestock.json` following the same pattern with appropriate required fields per the blueprint.

**Step 7: Commit**

```bash
git add backend/app/plugins/checklists/ backend/app/services/validation.py backend/tests/test_validation.py
git commit -m "feat: add checklist-based metadata validation with JSON Schema"
```

---

## Phase 7: Submissions & Validation Workflow

### Task 15: Submissions API with validation workflow

**Files:**
- Create: `backend/app/api/v1/submissions.py`
- Create: `backend/app/services/submissions.py`
- Test: `backend/tests/test_submissions_api.py`

The submission service must:
- Create submission in `draft` status
- `POST /submissions/{id}/validate` — run checklist validation on all linked samples, update status to `validated` or `failed`
- Track validation report as JSON

**TDD cycle: test -> implement -> pass -> commit**

**Commit message:** `feat: add Submissions API with validation workflow`

---

## Phase 8: Background Workers (QC)

### Task 16: Redis worker setup with arq

**Files:**
- Create: `backend/app/workers/main.py`
- Create: `backend/app/workers/qc.py`
- Test: `backend/tests/test_workers.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_workers.py
import pytest
from app.workers.qc import determine_qc_tool, check_thresholds
from app.models.enums import Platform


def test_determine_qc_tool_illumina():
    assert determine_qc_tool(Platform.ILLUMINA) == "fastqc"


def test_determine_qc_tool_nanopore():
    assert determine_qc_tool(Platform.OXFORD_NANOPORE) == "nanoplot"


def test_determine_qc_tool_snpchip():
    assert determine_qc_tool(Platform.SNP_CHIP) == "snpchip_qc"


def test_check_thresholds_pass():
    result = check_thresholds("fastqc", {"q30_percent": 92.3, "adapter_percent": 1.2, "duplication_rate": 8.5})
    assert result == "pass"


def test_check_thresholds_fail():
    result = check_thresholds("fastqc", {"q30_percent": 50.0, "adapter_percent": 1.2, "duplication_rate": 8.5})
    assert result == "fail"


def test_check_thresholds_warn():
    result = check_thresholds("fastqc", {"q30_percent": 80.0, "adapter_percent": 4.9, "duplication_rate": 29.0})
    assert result == "warn"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_workers.py -v`
Expected: FAIL

**Step 3: Write QC worker logic**

```python
# backend/app/workers/qc.py
from app.models.enums import Platform

QC_THRESHOLDS = {
    "fastqc": {
        "q30_percent": {"min": 80.0, "warn": 80.0},
        "adapter_percent": {"max": 5.0, "warn": 4.0},
        "duplication_rate": {"max": 30.0, "warn": 25.0},
    },
    "nanoplot": {
        "mean_read_length": {"min": 1000},
        "mean_quality": {"min": 10.0},
    },
    "snpchip_qc": {
        "call_rate": {"min": 0.95},
        "missing_rate": {"max": 0.05},
    },
}


def determine_qc_tool(platform: Platform) -> str:
    mapping = {
        Platform.ILLUMINA: "fastqc",
        Platform.OXFORD_NANOPORE: "nanoplot",
        Platform.PACBIO_SMRT: "nanoplot",
        Platform.SNP_CHIP: "snpchip_qc",
        Platform.HI_C: "fastqc",
    }
    return mapping[platform]


def check_thresholds(tool: str, metrics: dict) -> str:
    thresholds = QC_THRESHOLDS.get(tool, {})
    status = "pass"
    for metric, limits in thresholds.items():
        value = metrics.get(metric)
        if value is None:
            continue
        if "min" in limits and value < limits["min"]:
            return "fail"
        if "max" in limits and value > limits["max"]:
            return "fail"
        if "warn" in limits:
            if "min" in limits and value <= limits["warn"]:
                status = "warn"
            if "max" in limits and value >= limits["warn"]:
                status = "warn"
    return status
```

```python
# backend/app/workers/main.py
from arq import cron
from arq.connections import RedisSettings
from app.config import settings


async def run_qc_job(ctx, run_id: int):
    """Execute QC for a given run. Called by arq worker."""
    # Full implementation connects to DB, determines platform,
    # runs appropriate QC tool, stores results
    pass


class WorkerSettings:
    functions = [run_qc_job]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_workers.py -v`
Expected: PASS (6 passed)

**Step 5: Commit**

```bash
git add backend/app/workers/ backend/tests/test_workers.py
git commit -m "feat: add QC worker with threshold checking and platform-based tool selection"
```

---

## Phase 9: Search & Data Retrieval

### Task 17: Full-text search and filtered queries

**Files:**
- Create: `backend/app/api/v1/search.py`
- Create: `backend/app/services/search.py`
- Test: `backend/tests/test_search.py`

Implement:
- `GET /api/v1/search?q=...&type=study,sample` — full-text search using PostgreSQL `to_tsvector/to_tsquery`
- Filtered queries on existing entity endpoints (organism, platform, date range, breed, tax_id)
- Pagination with `page` and `per_page`

**TDD cycle: test -> implement -> pass -> commit**

**Commit message:** `feat: add full-text search and filtered queries across all entities`

---

### Task 18: Download and export endpoints

**Files:**
- Create: `backend/app/api/v1/downloads.py`
- Create: `backend/app/services/export.py`
- Test: `backend/tests/test_export.py`

Implement:
- `GET /runs/{accession}/download` — return presigned download URL from MinIO
- `GET /studies/{accession}/download-manifest?format=tsv` — bulk download manifest
- `GET /studies/{accession}/export?format=ena-xml` — ENA XML export
- `GET /studies/{accession}/export?format=jsonld` — JSON-LD export (FAIR)
- `GET /studies/{accession}/samples/export?format=tsv` — sample metadata export

**TDD cycle: test -> implement -> pass -> commit**

**Commit message:** `feat: add download URLs, export endpoints (ENA XML, JSON-LD, TSV)`

---

## Phase 10: ENA Submission (Phase 1 — Manual Export)

### Task 19: ENA XML generator

**Files:**
- Create: `backend/app/plugins/exporters/ena_xml.py`
- Test: `backend/tests/test_ena_xml.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_ena_xml.py
import pytest
from app.plugins.exporters.ena_xml import generate_study_xml, generate_sample_xml


def test_generate_study_xml():
    xml = generate_study_xml({
        "accession": "NFDP-PRJ-000001",
        "title": "Camel WGS",
        "description": "WGS of dromedary camels",
    })
    assert "<STUDY" in xml
    assert "Camel WGS" in xml
    assert "alias=\"NFDP-PRJ-000001\"" in xml


def test_generate_sample_xml():
    xml = generate_sample_xml({
        "accession": "NFDP-SAM-000001",
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "checklist_id": "ERC000055",
    })
    assert "<SAMPLE" in xml
    assert "9838" in xml
    assert "ERC000055" in xml
```

**Step 2-5: Implement using xml.etree.ElementTree, test, commit**

**Commit message:** `feat: add ENA XML generator for manual submission export`

---

## Phase 11: LIMS Integration

### Task 20: LIMS webhook receiver

**Files:**
- Create: `backend/app/api/v1/integrations.py`
- Create: `backend/app/services/lims.py`
- Test: `backend/tests/test_lims.py`

Implement:
- `POST /api/v1/integrations/lims/webhook` — receive LIMS events (sample_registered, library_prepared, sequencing_complete)
- HMAC signature verification via `X-LIMS-Signature` header
- Auto-create Sample/Experiment/Run records from LIMS events
- Field mapping per blueprint Section 11.3

**TDD cycle: test -> implement -> pass -> commit**

**Commit message:** `feat: add LIMS webhook integration with HMAC signature verification`

---

## Phase 12: Frontend

### Task 21: Initialize Next.js frontend

**Step 1: Create Next.js app**

```bash
cd frontend && npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --no-import-alias
```

**Step 2: Install dependencies**

```bash
cd frontend && npm install @tanstack/react-query axios lucide-react
npx shadcn@latest init
npx shadcn@latest add button card input table badge dialog form select tabs toast
```

**Step 3: Create API client**

```typescript
// frontend/src/lib/api.ts
import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;
```

**Step 4: Commit**

```bash
git add frontend/
git commit -m "feat: initialize Next.js frontend with shadcn/ui and API client"
```

---

### Task 22: Dashboard page

**Files:**
- Create: `frontend/src/app/dashboard/page.tsx`
- Create: `frontend/src/components/stats-cards.tsx`
- Create: `frontend/src/components/recent-submissions.tsx`

Dashboard displays:
- Total studies, samples, runs counts
- Recent submissions with status badges
- Storage usage summary
- QC status breakdown (pass/warn/fail)

**Commit message:** `feat: add dashboard page with stats cards and recent submissions`

---

### Task 23: Submission wizard (multi-step form)

**Files:**
- Create: `frontend/src/app/submit/page.tsx`
- Create: `frontend/src/components/wizard/study-step.tsx`
- Create: `frontend/src/components/wizard/samples-step.tsx`
- Create: `frontend/src/components/wizard/experiment-step.tsx`
- Create: `frontend/src/components/wizard/upload-step.tsx`
- Create: `frontend/src/components/wizard/review-step.tsx`

Multi-step wizard:
1. Create/select study
2. Register samples (form or CSV upload) — dynamic fields per checklist
3. Define experiment (platform, library details)
4. Upload files (drag-and-drop with progress)
5. Review and submit

**Commit message:** `feat: add multi-step submission wizard with dynamic checklist fields`

---

### Task 24: Data browser with search and filters

**Files:**
- Create: `frontend/src/app/browse/page.tsx`
- Create: `frontend/src/components/data-table.tsx`
- Create: `frontend/src/components/search-bar.tsx`
- Create: `frontend/src/components/filters.tsx`

Features:
- Full-text search bar
- Faceted filters: organism, platform, date range, project type
- Sortable, paginated data table
- Click-through to study/sample/run detail pages

**Commit message:** `feat: add data browser with search, filters, and pagination`

---

### Task 25: Upload manager with progress tracking

**Files:**
- Create: `frontend/src/components/upload-manager.tsx`
- Create: `frontend/src/hooks/use-upload.ts`

Features:
- Drag-and-drop file zone
- Client-side MD5 checksum computation (using spark-md5 in Web Worker)
- Multipart upload to presigned MinIO URL with progress bars
- Resume failed uploads

**Commit message:** `feat: add upload manager with client-side checksums and progress tracking`

---

### Task 26: QC report viewer

**Files:**
- Create: `frontend/src/app/runs/[accession]/qc/page.tsx`
- Create: `frontend/src/components/qc-summary.tsx`

Features:
- Display QC status badge (pass/warn/fail)
- Summary metrics table
- Embedded HTML report (iframe for FastQC/MultiQC)

**Commit message:** `feat: add QC report viewer with embedded HTML reports`

---

### Task 27: FAIR dashboard

**Files:**
- Create: `frontend/src/app/fair/page.tsx`
- Create: `frontend/src/components/fair-score.tsx`

Features:
- Per-study FAIR compliance score (radar chart)
- Missing metadata alerts
- License coverage percentage
- Public deposition rate

**Commit message:** `feat: add FAIR compliance dashboard with per-study scoring`

---

### Task 28: Admin panel

**Files:**
- Create: `frontend/src/app/admin/page.tsx`
- Create: `frontend/src/app/admin/users/page.tsx`
- Create: `frontend/src/app/admin/ena/page.tsx`

Features:
- User management (list, create, change roles)
- System statistics
- ENA submission management (export XML, view submission status)
- Pipeline configuration

**Commit message:** `feat: add admin panel with user management and ENA submission tools`

---

## Phase 13: Integration Testing & Docker

### Task 29: Integration test suite

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_integration.py`

**Step 1: Write conftest with test database**

```python
# backend/tests/conftest.py
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.database import Base, get_db
from app.services.auth import hash_password, create_access_token
from app.models.user import User
from app.models.enums import UserRole

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSession() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db):
    async def override_db():
        yield db
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(db):
    user = User(
        email="test@nfdp.sa",
        hashed_password=hash_password("testpass"),
        full_name="Test User",
        role=UserRole.ADMIN,
    )
    db.add(user)
    await db.commit()
    token = create_access_token(data={"sub": user.email, "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}
```

**Step 2: Write end-to-end test**

```python
# backend/tests/test_integration.py
import pytest


@pytest.mark.asyncio
async def test_full_deposition_workflow(client, auth_headers):
    # 1. Create study
    r = await client.post("/api/v1/studies", json={
        "title": "Integration Test Study",
        "description": "Testing full workflow",
        "project_type": "WGS",
    }, headers=auth_headers)
    assert r.status_code == 201
    study_acc = r.json()["accession"]
    assert study_acc.startswith("NFDP-PRJ-")

    # 2. Create sample
    r = await client.post("/api/v1/samples", json={
        "study_accession": study_acc,
        "checklist_id": "ERC000055",
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "collection_date": "2026-01-15",
        "geographic_location": "Saudi Arabia:Riyadh",
    }, headers=auth_headers)
    assert r.status_code == 201
    sample_acc = r.json()["accession"]

    # 3. Create experiment
    r = await client.post("/api/v1/experiments", json={
        "sample_accession": sample_acc,
        "platform": "ILLUMINA",
        "instrument_model": "NovaSeq 6000",
        "library_strategy": "WGS",
        "library_source": "GENOMIC",
        "library_layout": "PAIRED",
        "insert_size": 350,
    }, headers=auth_headers)
    assert r.status_code == 201

    # 4. Verify study lists correctly
    r = await client.get("/api/v1/studies")
    assert r.status_code == 200
    assert len(r.json()) == 1

    # 5. Verify search
    r = await client.get(f"/api/v1/studies/{study_acc}")
    assert r.status_code == 200
    assert r.json()["title"] == "Integration Test Study"
```

**Step 3: Run tests**

Run: `cd backend && python -m pytest tests/ -v --tb=short`
Expected: ALL PASS

**Step 4: Commit**

```bash
git add backend/tests/
git commit -m "test: add integration test suite with full deposition workflow"
```

---

### Task 30: Docker Compose full stack verification

**Step 1: Build and start all services**

```bash
docker compose build
docker compose up -d
```

**Step 2: Wait for services, run migrations**

```bash
docker compose exec backend alembic upgrade head
```

**Step 3: Create MinIO buckets**

```bash
docker compose exec backend python -c "from app.services.storage import storage_service; storage_service.ensure_buckets()"
```

**Step 4: Verify health**

```bash
curl http://localhost:8000/api/v1/health
# Expected: {"status":"healthy","version":"0.1.0"}

curl http://localhost:3000
# Expected: Next.js frontend loads
```

**Step 5: Run full test suite against Docker**

```bash
docker compose exec backend python -m pytest tests/ -v
```

**Step 6: Commit any fixes**

```bash
git commit -m "chore: verify full Docker Compose stack works end-to-end"
```

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | 1-2 | Project scaffolding, Docker Compose, FastAPI skeleton |
| 2 | 3-5 | Data model, accessions, SQLAlchemy models, Alembic |
| 3 | 6-7 | Pydantic schemas, JWT authentication |
| 4 | 8-11 | CRUD APIs for Study, Sample, Experiment, Run |
| 5 | 12-13 | MinIO storage, presigned upload flow |
| 6 | 14 | Checklist-based metadata validation |
| 7 | 15 | Submissions workflow |
| 8 | 16 | Background QC workers |
| 9 | 17-18 | Search, download, export endpoints |
| 10 | 19 | ENA XML generator |
| 11 | 20 | LIMS webhook integration |
| 12 | 21-28 | Next.js frontend (all pages) |
| 13 | 29-30 | Integration tests, Docker verification |

**Total: 30 tasks across 13 phases.**
