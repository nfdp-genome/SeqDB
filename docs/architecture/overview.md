# System Overview

The SeqDB Genomic Deposition System is a full-stack web application for managing genomic data submissions.

## Architecture

```mermaid
graph TB
    subgraph Frontend
        UI[Next.js Web App<br/>React + shadcn/ui]
    end

    subgraph Backend
        API[FastAPI REST API]
        Workers[Background Workers<br/>QC, ENA sync]
    end

    subgraph Storage
        DB[(PostgreSQL<br/>Metadata)]
        OBJ[MinIO / S3<br/>Sequence Files]
        CACHE[Redis<br/>Job Queue]
    end

    subgraph External
        ENA[ENA<br/>European Nucleotide Archive]
        LIMS[LIMS<br/>Lab Information System]
    end

    UI -->|REST API| API
    API --> DB
    API --> OBJ
    API --> CACHE
    Workers --> DB
    Workers --> OBJ
    Workers --> CACHE
    Workers -->|Submit| ENA
    LIMS -->|Webhook| API
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), Pydantic v2 |
| Database | PostgreSQL (production), SQLite (dev) |
| Object Storage | MinIO (S3-compatible) |
| Job Queue | Redis + ARQ |
| Auth | JWT (JSON Web Tokens) |

## Data Flow

### Submission flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant MinIO
    participant DB

    User->>Frontend: Upload FASTQ files
    Frontend->>API: POST /staging/upload
    API->>MinIO: Store in staging bucket
    API->>DB: Register staged file

    User->>Frontend: Upload sample sheet
    Frontend->>API: POST /bulk-submit/validate
    API->>DB: Query staged files
    API-->>Frontend: Validation report

    User->>Frontend: Confirm submission
    Frontend->>API: POST /bulk-submit/confirm
    API->>DB: Create Sample, Experiment, Run
    API->>MinIO: Link files to runs
    API-->>Frontend: Created accessions
```

### Download flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant MinIO

    Client->>API: GET /filereport?accession=NFDP-PRJ-000001
    API-->>Client: File metadata + download URLs

    Client->>API: GET /runs/NFDP-RUN-000001/download
    API->>MinIO: Generate presigned URL
    API-->>Client: 307 Redirect to presigned URL
    Client->>MinIO: Download file directly
```

## Directory structure

```
pathogen_genomics/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # DB connection
│   │   └── main.py          # FastAPI app
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/      # React components
│   │   └── lib/             # API client, utilities
│   └── public/
├── docs/                    # This documentation
├── docker-compose.yml       # Local dev services
└── mkdocs.yml              # Docs configuration
```
