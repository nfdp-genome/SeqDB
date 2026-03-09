# NFDP Genomic Data Deposition System — Blueprint

**Version:** 1.0
**Date:** 2026-03-06
**Status:** Approved
**Project:** National Livestock and Food Data Platform (NLFDP) — Pathogen Genomics

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Data Model (ENA/INSDC)](#3-data-model-enainsdc)
4. [Metadata Standards & Checklists](#4-metadata-standards--checklists)
5. [SNP Chip Metadata Schema](#5-snp-chip-metadata-schema)
6. [FAIR Data Principles](#6-fair-data-principles)
7. [API Specification](#7-api-specification)
8. [File Upload & Storage](#8-file-upload--storage)
9. [QC & Pipeline Integration](#9-qc--pipeline-integration)
10. [User Interface](#10-user-interface)
11. [LIMS Integration](#11-lims-integration)
12. [ENA Public Submission Pathway](#12-ena-public-submission-pathway)
13. [Extensibility](#13-extensibility)
14. [Deployment Strategy](#14-deployment-strategy)

---

## 1. Executive Summary

The NFDP Genomic Data Deposition System is an internal genomic data archive with a pathway for public deposition to ENA/NCBI. It serves a sequencing facility producing 50-200 TB/year of data across multiple platforms (Illumina, ONT, PacBio, SNP chip, Hi-C) for livestock (camel, sheep, horse, goat, bovine) and their pathogens.

**Core goals:**

- Centralized, searchable archive for all sequencing and genotyping output
- ENA/INSDC-compatible metadata from day one
- FAIR-compliant data management
- Automated QC, validation, and pipeline triggering
- Phased public submission to ENA/NCBI
- LIMS integration for end-to-end lab-to-archive traceability
- Extensible architecture that grows with the facility

**Tech stack:** Next.js (frontend), FastAPI (backend), PostgreSQL (metadata), MinIO (object storage), Redis (job queue), Nextflow (pipelines).

---

## 2. System Architecture

### 2.1 Overview

```
+-----------------------------------------------------------+
|                      CLOUD LAYER                          |
|  +---------------+  +---------------+  +---------------+  |
|  |   Next.js     |  |   FastAPI     |  |  PostgreSQL   |  |
|  |   (Frontend)  |--|   (Backend)   |--|  (Metadata)   |  |
|  +---------------+  +-------+-------+  +---------------+  |
|                            |                               |
|                     +------+-------+                       |
|                     |    Redis     |                       |
|                     |  (Job Queue) |                       |
|                     +------+-------+                       |
+----------------------------+-------------------------------+
                             | VPN / Secure Tunnel
+----------------------------+-------------------------------+
|                      ON-PREM LAYER                        |
|                     +------+-------+                       |
|                     |    MinIO     |                       |
|                     | (Object Str) |                       |
|                     +------+-------+                       |
|                            |                               |
|          +-----------------+-----------------+             |
|    +-----+------+   +------+-------+   +-----+------+    |
|    |  Nextflow  |   |   Worker     |   |  ENA/NCBI  |    |
|    | (Pipelines)|   |  (QC/Valid)  |   | (Submitter)|    |
|    +------------+   +--------------+   +------------+    |
+-----------------------------------------------------------+
```

### 2.2 Key Decisions

- **Cloud layer:** Portal, API, and metadata DB for external client access
- **On-prem layer:** Bulk data (MinIO), pipelines (Nextflow), workers close to sequencers
- **Connection:** Secure VPN tunnel between layers
- **Development:** Everything runs locally; cloud split only at production deployment

---

## 3. Data Model (ENA/INSDC)

The data model follows the ENA/INSDC hierarchy directly.

### 3.1 Core Entities

**Study (Project)**

| Field              | Type     | Required | Description                                          |
|--------------------|----------|----------|------------------------------------------------------|
| internal_accession | string   | Yes      | Format: `NFDP-PRJ-000001`                            |
| ena_accession      | string   | No       | Format: `PRJEB______` (after public submission)      |
| title              | string   | Yes      | Study title                                          |
| description        | text     | Yes      | Study abstract                                       |
| release_date       | date     | No       | Embargo release date                                 |
| project_type       | enum     | Yes      | WGS, Metagenomics, Genotyping, Transcriptomics, etc. |
| created_by         | FK(User) | Yes      | Submitting user                                      |

**Sample**

| Field               | Type      | Required | Description                       |
|---------------------|-----------|----------|-----------------------------------|
| internal_accession  | string    | Yes      | Format: `NFDP-SAM-000001`         |
| ena_accession       | string    | No       | Format: `ERS________`             |
| organism            | string    | Yes      | Species name                      |
| tax_id              | integer   | Yes      | NCBI Taxonomy ID                  |
| breed               | string    | No       | Breed/strain name                 |
| collection_date     | date      | Yes      | Sample collection date            |
| geographic_location | string    | Yes      | Country:Region                    |
| host                | string    | No       | Host organism (for pathogens)     |
| tissue              | string    | No       | Tissue/source                     |
| developmental_stage | string    | No       | Age/stage                         |
| checklist_id        | string    | Yes      | ENA checklist used for validation |
| study               | FK(Study) | Yes      | Parent study                      |

**Experiment**

| Field              | Type       | Required | Description                                            |
|--------------------|------------|----------|--------------------------------------------------------|
| internal_accession | string     | Yes      | Format: `NFDP-EXP-000001`                              |
| ena_accession      | string     | No       | Format: `ERX________`                                  |
| platform           | enum       | Yes      | ILLUMINA, OXFORD_NANOPORE, PACBIO_SMRT, SNP_CHIP, HI_C |
| instrument_model   | string     | Yes      | E.g., NovaSeq 6000, MinION, Sequel II                  |
| library_strategy   | enum       | Yes      | WGS, WXS, RNA-Seq, AMPLICON, etc.                      |
| library_source     | enum       | Yes      | GENOMIC, TRANSCRIPTOMIC, METAGENOMIC                   |
| library_layout     | enum       | Yes      | PAIRED, SINGLE                                         |
| insert_size        | integer    | No       | Fragment size for paired-end                           |
| sample             | FK(Sample) | Yes      | Parent sample                                          |

**Run**

| Field              | Type           | Required | Description                              |
|--------------------|----------------|----------|------------------------------------------|
| internal_accession | string         | Yes      | Format: `NFDP-RUN-000001`                |
| ena_accession      | string         | No       | Format: `ERR________`                    |
| file_type          | enum           | Yes      | FASTQ, BAM, CRAM, VCF, IDAT, BED/BIM/FAM |
| file_path          | string         | Yes      | MinIO bucket/key path                    |
| file_size          | bigint         | Yes      | File size in bytes                       |
| checksum_md5       | string         | Yes      | MD5 hash                                 |
| checksum_sha256    | string         | Yes      | SHA-256 hash                             |
| experiment         | FK(Experiment) | Yes      | Parent experiment                        |

### 3.2 Supporting Entities

**Submission** — Groups a batch of entities, tracks lifecycle: `draft -> validated -> deposited -> published`

**QC Report** — Linked to Run, stores QC tool output and pass/fail status

**Pipeline Job** — Tracks Nextflow execution tied to Runs

**User** — Internal staff or external client with role-based access

### 3.3 Accession Format

All internal accessions follow: `NFDP-{TYPE}-{6-digit-sequence}`

| Type       | Prefix | Example         |
|------------|--------|-----------------|
| Study      | PRJ    | NFDP-PRJ-000001 |
| Sample     | SAM    | NFDP-SAM-000001 |
| Experiment | EXP    | NFDP-EXP-000001 |
| Run        | RUN    | NFDP-RUN-000001 |
| Submission | SUB    | NFDP-SUB-000001 |

---

## 4. Metadata Standards & Checklists

### 4.1 ENA Checklists Adopted

| Checklist ID | Name                              | Use Case                        |
|--------------|-----------------------------------|---------------------------------|
| ERC000011    | ENA default sample                | General-purpose catch-all       |
| ERC000020    | Pathogen clinical/host-associated | Pathogens from livestock hosts  |
| ERC000028    | Pathogen environment/food         | Environmental pathogen isolates |
| ERC000043    | ENA virus pathogen reporting      | Viral pathogens                 |
| ERC000055    | Farm animal                       | Livestock samples               |

### 4.2 Validation Pipeline

```
Submission --> Schema Validation --> Checklist Validation --> Taxonomy Check --> Accept/Reject
                    |                      |                       |
              JSON Schema           ENA checklist rules      NCBI Taxonomy ID
            (field types,          (required fields per       (valid organism
             formats)               sample type)               + strain)
```

### 4.3 Implementation

- Checklist definitions stored as JSON schemas, importable/updatable from ENA's checklist API
- Each Sample tagged with a checklist ID; validation runs against that checklist
- Mandatory fields (all checklists): `organism`, `tax_id`, `collection_date`, `geographic_location`
- Domain-specific fields auto-appear based on checklist selection
- Custom fields allowed via key-value extension for internal metadata not in ENA

---

## 5. SNP Chip Metadata Schema

SNP chip data is not covered by ENA sequencing checklists. This custom schema follows the same validation pattern.

### 5.1 Common Fields (All Species)

| Field               | Required | Description                                                |
|---------------------|----------|------------------------------------------------------------|
| organism            | Yes      | Species name                                               |
| tax_id              | Yes      | NCBI taxonomy ID                                           |
| breed               | Yes      | Breed name (e.g., Najdi, Awassi, Arabian)                  |
| sample_id           | Yes      | Internal animal/sample ID                                  |
| chip_type           | Yes      | Array product name                                         |
| chip_version        | Yes      | Array version/revision                                     |
| chip_manufacturer   | Yes      | Illumina, Affymetrix, Thermo Fisher                        |
| chip_density        | Yes      | Low (<=20K), Medium (50K), High (>=150K), HD (>=600K)      |
| total_snps_on_chip  | Yes      | Total markers on array                                     |
| snps_called         | Yes      | Number of successfully genotyped markers                   |
| call_rate           | Yes      | Percentage (e.g., 0.98)                                    |
| call_rate_threshold | Yes      | Minimum acceptable (e.g., 0.95)                            |
| genotyping_software | Yes      | GenomeStudio, Axiom Analysis Suite, etc.                   |
| software_version    | Yes      | Version of genotyping software                             |
| cluster_file        | No       | Custom cluster file used                                   |
| reference_genome    | Yes      | Assembly (e.g., CamDro3, ARS-UCD1.2)                       |
| collection_date     | Yes      | Sample collection date                                     |
| geographic_location | Yes      | Country/region                                             |
| sex                 | Yes      | Male / Female / Unknown                                    |
| tissue_source       | Yes      | Blood, ear punch, hair, semen                              |
| purpose             | Yes      | GWAS, parentage, genomic_selection, breed_characterization |
| project_id          | Yes      | Linked NFDP Study accession                                |

### 5.2 Species-Specific Chip Catalog

| Species | Common Chips                      | Density    |
|---------|-----------------------------------|------------|
| Camel   | Axiom Camel Genotyping Array      | ~80K       |
| Sheep   | Illumina OvineSNP50, OvineHD      | 50K / 600K |
| Goat    | Illumina GoatSNP50                | 50K        |
| Horse   | Illumina EquineSNP50, EquineSNP70 | 50K / 70K  |
| Bovine  | Illumina BovineSNP50, BovineHD    | 50K / 777K |

### 5.3 QC Fields

| Field           | Required | Description                                |
|-----------------|----------|--------------------------------------------|
| het_rate        | Yes      | Heterozygosity rate                        |
| missing_rate    | Yes      | Per-sample missing genotype rate           |
| duplicate_check | No       | Identity-by-descent flag                   |
| sex_check_pass  | No       | Reported vs. genotypic sex concordance     |
| plate_id        | No       | Lab plate identifier                       |
| well_position   | No       | Well position (e.g., A01)                  |
| batch_id        | No       | Genotyping batch for batch-effect tracking |

### 5.4 Output Files

| File Type      | Format                      | Description                     |
|----------------|-----------------------------|---------------------------------|
| Raw intensity  | .idat                       | Raw scanner output (Illumina)   |
| Genotype calls | .ped/.map or .bed/.bim/.fam | PLINK format                    |
| Final report   | .csv/.txt                   | GenomeStudio/Axiom final report |
| VCF            | .vcf.gz                     | Variant call format (optional)  |
| QC report      | .html/.pdf                  | Summary statistics              |

---

## 6. FAIR Data Principles

The system implements FAIR (Findable, Accessible, Interoperable, Reusable) principles throughout.

### 6.1 Findable

| Principle                                 | Implementation                                                                                                                                                                                         |
|-------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **F1. Globally unique identifiers**       | Every entity receives a persistent NFDP accession (`NFDP-PRJ-000001`). Upon public deposition, ENA accessions are linked.                                                                              |
| **F2. Rich metadata**                     | ENA checklists enforce comprehensive metadata. Custom fields extend coverage for internal needs.                                                                                                       |
| **F3. Metadata includes identifier**      | All metadata records contain their own accession and link to parent/child entities.                                                                                                                    |
| **F4. Registered in searchable resource** | Internal data browser with full-text search, faceted filtering by organism, platform, date, study. API supports programmatic discovery via `/api/v1/studies`, `/api/v1/samples` with query parameters. |

### 6.2 Accessible

| Principle | Implementation |
|-----------|---------------|
| **A1. Retrievable by identifier** | Every entity accessible via `GET /api/v1/{entity}/{accession}`. File downloads via presigned URLs. |
| **A1.1 Open protocol** | HTTPS-based REST API. No proprietary protocols. |
| **A1.2 Authentication where needed** | JWT-based auth. Public data accessible without login. Embargoed data requires authentication. |
| **A2. Metadata persists** | Metadata stored in PostgreSQL with full audit trail. Even if data files are removed, metadata records persist with tombstone status. |

### 6.3 Interoperable

| Principle | Implementation |
|-----------|---------------|
| **I1. Formal knowledge representation** | JSON-LD metadata with schema.org/bioschemas vocabulary. ENA XML for public submissions. |
| **I2. FAIR vocabularies** | NCBI Taxonomy for organisms. ENA controlled vocabularies for platforms, library strategies, file types. OBI ontology for experiment types. |
| **I3. Qualified references** | Explicit typed links between entities (Study hasMany Samples, Sample hasMany Experiments). Cross-references to external databases (BioSamples, Taxonomy, PubMed). |

### 6.4 Reusable

| Principle | Implementation |
|-----------|---------------|
| **R1. Rich provenance** | Every entity tracks: who created it, when, which submission, QC status, pipeline versions used. |
| **R1.1 Clear license** | Each study specifies a data use license (CC0, CC-BY, restricted). Displayed on portal and embedded in metadata exports. |
| **R1.2 Detailed provenance** | Full audit log: creation, modifications, QC events, pipeline runs, ENA submissions. Immutable event log. |
| **R1.3 Community standards** | ENA/INSDC metadata model. Standard file formats (FASTQ, BAM, VCF, PLINK). Validated against community checklists. |

### 6.5 FAIR Metrics Dashboard

The portal includes a FAIR compliance dashboard:

- **Per-study FAIR score** — percentage of FAIR criteria met
- **Missing metadata alerts** — highlights incomplete fields that reduce FAIRness
- **License coverage** — percentage of studies with explicit licenses
- **Public deposition rate** — percentage of eligible data submitted to ENA
- **Identifier resolution** — all accessions resolvable via API

---

## 7. API Specification

### 7.1 Base URL

```
Development: http://localhost:8000/api/v1
Production:  https://genomics.nfdp.sa/api/v1
```

### 7.2 Authentication

```
POST /api/v1/auth/login
  Request:  { "email": "user@nfdp.sa", "password": "..." }
  Response: { "access_token": "eyJ...", "refresh_token": "...", "expires_in": 3600 }

POST /api/v1/auth/refresh
  Request:  { "refresh_token": "..." }
  Response: { "access_token": "eyJ...", "expires_in": 3600 }

# All subsequent requests include:
Authorization: Bearer <access_token>
```

### 7.3 Data Deposition (Submitting Data)

**Step 1: Create a Study**

```
POST /api/v1/studies
Content-Type: application/json

{
  "title": "Camel WGS Riyadh 2026",
  "description": "Whole genome sequencing of dromedary camels from Riyadh region",
  "project_type": "WGS",
  "release_date": "2027-01-01"
}

Response 201:
{
  "accession": "NFDP-PRJ-000042",
  "title": "Camel WGS Riyadh 2026",
  "status": "active",
  "created_at": "2026-03-06T10:00:00Z"
}
```

**Step 2: Register Samples**

```
POST /api/v1/samples
{
  "study_accession": "NFDP-PRJ-000042",
  "checklist_id": "ERC000055",
  "organism": "Camelus dromedarius",
  "tax_id": 9838,
  "breed": "Najdi",
  "collection_date": "2026-01-15",
  "geographic_location": "Saudi Arabia:Riyadh",
  "sex": "female",
  "tissue": "blood"
}

Response 201:
{ "accession": "NFDP-SAM-000108", ... }
```

**Bulk sample registration:**

```
POST /api/v1/samples/bulk
Content-Type: multipart/form-data

file: samples.tsv   (TSV with columns matching checklist fields)
study_accession: NFDP-PRJ-000042
checklist_id: ERC000055

Response 201:
{
  "created": 48,
  "errors": 2,
  "error_details": [
    { "row": 12, "field": "tax_id", "message": "Invalid taxonomy ID" },
    { "row": 37, "field": "collection_date", "message": "Future date not allowed" }
  ]
}
```

**Step 3: Create Experiment**

```
POST /api/v1/experiments
{
  "sample_accession": "NFDP-SAM-000108",
  "platform": "ILLUMINA",
  "instrument_model": "NovaSeq 6000",
  "library_strategy": "WGS",
  "library_source": "GENOMIC",
  "library_layout": "PAIRED",
  "insert_size": 350
}

Response 201:
{ "accession": "NFDP-EXP-000095", ... }
```

**Step 4: Upload Files**

```
# Initiate upload — get presigned URL
POST /api/v1/upload/initiate
{
  "experiment_accession": "NFDP-EXP-000095",
  "filename": "camel_sample1_R1.fastq.gz",
  "file_size": 5368709120,
  "checksum_md5": "d41d8cd98f00b204e9800998ecf8427e",
  "file_type": "FASTQ"
}

Response 200:
{
  "upload_id": "up-a1b2c3d4",
  "presigned_url": "https://minio.local/nfdp-raw/...",
  "expires_in": 86400
}

# Client uploads directly to MinIO via presigned URL
PUT <presigned_url> --data-binary @camel_sample1_R1.fastq.gz

# Confirm upload
POST /api/v1/upload/complete
{
  "upload_id": "up-a1b2c3d4",
  "checksum_md5": "d41d8cd98f00b204e9800998ecf8427e"
}

Response 200:
{
  "run_accession": "NFDP-RUN-000201",
  "qc_job_id": "qc-e5f6g7h8",
  "status": "uploaded"
}
```

**Step 5: Create Submission**

```
POST /api/v1/submissions
{
  "title": "Camel WGS batch 1",
  "study_accession": "NFDP-PRJ-000042",
  "run_accessions": ["NFDP-RUN-000201", "NFDP-RUN-000202"]
}

Response 201:
{
  "submission_id": "NFDP-SUB-000015",
  "status": "draft"
}

# Trigger validation
POST /api/v1/submissions/NFDP-SUB-000015/validate

Response 200:
{
  "status": "validated",
  "errors": [],
  "warnings": ["Sample NFDP-SAM-000108: developmental_stage is empty"]
}
```

### 7.4 Data Retrieval (Fetching Data)

**Search and browse:**

```
# List studies with filtering
GET /api/v1/studies?organism=Camelus+dromedarius&platform=ILLUMINA&page=1&per_page=20

# Get study with all linked entities
GET /api/v1/studies/NFDP-PRJ-000042?expand=samples,experiments,runs

# Search samples across all studies
GET /api/v1/samples?tax_id=9838&breed=Najdi&date_from=2026-01-01

# Full-text search across all metadata
GET /api/v1/search?q=dromedary+riyadh+wgs&type=study,sample
```

**Download data:**

```
# Get download URL for a run's files
GET /api/v1/runs/NFDP-RUN-000201/download

Response 200:
{
  "files": [
    {
      "filename": "camel_sample1_R1.fastq.gz",
      "size": 5368709120,
      "checksum_md5": "d41d8cd98f00b204e9800998ecf8427e",
      "download_url": "https://minio.local/...",   // presigned, expires in 24h
      "expires_in": 86400
    }
  ]
}

# Bulk download manifest (for tools like wget/aria2)
GET /api/v1/studies/NFDP-PRJ-000042/download-manifest?format=tsv

Response 200:
# TSV with columns: url, filename, md5, size
```

**QC reports:**

```
GET /api/v1/runs/NFDP-RUN-000201/qc

Response 200:
{
  "status": "pass",
  "tool": "FastQC",
  "summary": {
    "total_reads": 42000000,
    "q30_percent": 92.3,
    "adapter_percent": 1.2,
    "duplication_rate": 8.5
  },
  "report_url": "https://minio.local/nfdp-qc/NFDP-RUN-000201/multiqc_report.html"
}
```

**Export metadata:**

```
# Export as ENA-compatible XML
GET /api/v1/studies/NFDP-PRJ-000042/export?format=ena-xml

# Export as JSON-LD (FAIR/schema.org)
GET /api/v1/studies/NFDP-PRJ-000042/export?format=jsonld

# Export sample metadata as TSV
GET /api/v1/studies/NFDP-PRJ-000042/samples/export?format=tsv
```

### 7.5 Programmatic Client (Python SDK)

```python
from nfdp_client import NFDPClient

client = NFDPClient("https://genomics.nfdp.sa/api/v1", token="eyJ...")

# Create study
study = client.create_study(
    title="Camel WGS Riyadh 2026",
    project_type="WGS"
)

# Bulk register samples from TSV
results = client.register_samples_bulk(
    study_accession=study.accession,
    tsv_file="samples.tsv",
    checklist_id="ERC000055"
)

# Upload files
client.upload(
    experiment_accession="NFDP-EXP-000095",
    files=["sample1_R1.fastq.gz", "sample1_R2.fastq.gz"]
)

# Search
samples = client.search_samples(organism="Camelus dromedarius", breed="Najdi")
```

---

## 8. File Upload & Storage

### 8.1 Upload Flow

```
User/Sequencer                    FastAPI                     MinIO
     |                               |                          |
     |-- POST /upload/initiate ----->|                          |
     |   (filename, size, md5)       |-- Generate presigned --->|
     |                               |<-- Return URL -----------|
     |<-- presigned URL -------------|                          |
     |                               |                          |
     |-- PUT (direct upload) --------+------------------------->|
     |   (multipart, resumable)      |                          |
     |                               |                          |
     |-- POST /upload/complete ----->|                          |
     |   (upload_id, client_md5)     |-- Verify checksum ------>|
     |                               |<-- Match ----------------|
     |                               |-- Register in DB         |
     |                               |-- Queue QC job --> Redis  |
     |<-- 200 OK + Run accession ----|                          |
```

### 8.2 Storage Layout

```
nfdp-raw/           # Immutable raw data (write-once)
  {study_accession}/{sample_accession}/{run_accession}/
    sample1_R1.fastq.gz
    sample1_R2.fastq.gz
    checksums.md5

nfdp-qc/            # QC reports and metrics
  {run_accession}/
    fastqc_R1.html
    multiqc_report.html

nfdp-processed/     # Pipeline output
  {run_accession}/
    aligned.bam
    variants.vcf.gz

nfdp-snpchip/       # Genotyping data
  {study_accession}/{sample_accession}/
    raw.idat
    genotypes.bed/.bim/.fam
    final_report.csv
```

### 8.3 Storage Policies

- **Immutable raw data** — raw bucket is write-once; no overwrites or deletes without admin approval
- **Resumable multipart uploads** — critical for large files over unstable connections
- **Double checksum** — client computes MD5 before upload, server verifies after
- **Separate buckets** — raw, QC, processed, SNP chip have different retention and access policies
- **Lifecycle rules** — processed data can be re-generated; configurable retention per bucket

---

## 9. QC & Pipeline Integration

### 9.1 QC Flow

```
Upload Complete --> Redis Queue --> Worker picks up job
                                        |
                    +-------------------+-------------------+
                    |                   |                   |
              Short Reads          Long Reads          SNP Chip
                    |                   |                   |
              FastQC / fastp     NanoPlot / NanoStat   Call Rate
              MultiQC            pycoQC                Het Rate
                    |                   |               Sex Check
                    |                   |                   |
                    +-------------------+-------------------+
                                        |
                                   QC Pass/Fail
                                        |
                          +-------------+-------------+
                          |             |             |
                        Pass          Warn          Fail
                          |             |             |
                    Mark valid    Flag review     Notify user
                          |             |          (reject)
                          +------+------+
                                 |
                     Optional: Trigger Nextflow pipeline
```

### 9.2 QC Thresholds (Configurable)

| Data Type | Metric | Default Threshold |
|-----------|--------|-------------------|
| Short reads | Q30 bases | >= 80% |
| Short reads | Adapter content | <= 5% |
| Short reads | Duplication rate | <= 30% |
| Long reads | Mean read length | >= 1 Kbp |
| Long reads | Mean quality | >= Q10 |
| SNP chip | Call rate | >= 0.95 |
| SNP chip | Missing rate | <= 0.05 |

### 9.3 Nextflow Integration

- Pipelines stored as versioned Nextflow scripts in `pipelines/` directory
- Worker triggers pipeline via Nextflow CLI, passing MinIO paths as input
- Pipeline output written to `nfdp-processed/` bucket
- Job status tracked in DB; users see progress in portal

### 9.4 Notifications

- QC complete: email + in-app notification to submitter
- QC failure: email with report link + flagged in dashboard
- Pipeline complete: email with results link

---

## 10. User Interface

### 10.1 Portal Screens

| Screen | Purpose | Users |
|--------|---------|-------|
| Dashboard | Overview: submissions, QC status, storage, pending actions | All |
| Submission Wizard | Step-by-step: Study -> Samples -> Experiment -> Upload | Submitters |
| Sample Registration | Form or CSV/TSV bulk upload, dynamic checklist fields | Submitters |
| Upload Manager | Drag-and-drop, progress bars, resumable, checksums | Submitters |
| Submission Tracker | Status timeline: draft -> validated -> deposited -> published | All |
| Data Browser | Search/filter across studies, samples, runs | All |
| QC Reports | Interactive FastQC/MultiQC/NanoPlot reports | All |
| FAIR Dashboard | Per-study FAIR score, compliance metrics | All |
| ENA Submission | Review, generate XML, submit | Admins |
| Admin Panel | Users, stats, storage, pipeline config | Admins |

### 10.2 Submission Wizard Flow

```
1. Create/Select Study
        |
2. Register Samples (form or CSV bulk)
   +-- Select checklist --> dynamic fields appear
        |
3. Define Experiments (platform, library details)
        |
4. Upload Files (drag-and-drop, link to runs)
   +-- Auto-checksum + progress tracking
        |
5. Review & Submit
   +-- Validation runs --> fix errors or proceed
        |
6. Submission Created (status: draft --> validated)
```

### 10.3 Access Control

| Role | Permissions |
|------|------------|
| Admin | Full access, user management, ENA submission, pipeline config |
| Submitter | Create studies/samples/experiments, upload data, view own submissions |
| Viewer | Browse and download published data only |
| External Client | Submitter permissions scoped to their own projects |

---

## 11. LIMS Integration

### 11.1 Integration Architecture

```
LIMS (Laboratory)                    NFDP Deposition System
     |                                        |
     |-- Webhook: sample_registered --------->|  Auto-create Sample
     |-- Webhook: library_prepared ---------->|  Auto-create Experiment
     |-- Webhook: sequencing_complete ------->|  Auto-initiate upload
     |                                        |
     |<-- API: GET /samples/{accession} ------|  LIMS queries status
     |<-- API: GET /runs/{accession}/qc ------|  LIMS pulls QC results
     |                                        |
     |<-- Webhook: qc_complete ---------------|  Notify LIMS of QC result
     |<-- Webhook: submission_validated ------|  Notify LIMS of validation
```

### 11.2 Integration Methods

**Method A: Webhook-driven (recommended)**

The LIMS pushes events to the deposition system as samples progress through the lab:

```
POST /api/v1/integrations/lims/webhook
X-LIMS-Signature: sha256=...

{
  "event": "sequencing_complete",
  "lims_sample_id": "LIMS-2026-0042",
  "lims_run_id": "NV-20260306-001",
  "instrument": "NovaSeq 6000",
  "output_path": "/data/sequencer/output/20260306_run001/",
  "files": [
    { "filename": "sample1_R1.fastq.gz", "md5": "abc123..." },
    { "filename": "sample1_R2.fastq.gz", "md5": "def456..." }
  ]
}
```

**Method B: Polling API**

The deposition system periodically queries the LIMS for new data:

```
GET https://lims.internal/api/runs?status=complete&since=2026-03-06T00:00:00Z
```

**Method C: Shared filesystem watch**

A watcher monitors the sequencer output directory and auto-ingests completed runs:

```
/data/sequencer/output/
  +-- 20260306_run001/        <-- watcher detects RTAComplete.txt
      +-- sample1_R1.fastq.gz
      +-- sample1_R2.fastq.gz
      +-- SampleSheet.csv     <-- parsed for metadata
```

### 11.3 LIMS Field Mapping

| LIMS Field | NFDP Field | Notes |
|-----------|------------|-------|
| lims_sample_id | external_id | Stored as cross-reference |
| lims_project_id | study.external_id | Links to NFDP Study |
| sample_name | sample.alias | Display name |
| species | sample.organism | Mapped to taxonomy |
| extraction_method | experiment.library_construction_protocol | Lab protocol |
| library_kit | experiment.library_kit | Prep kit used |
| flowcell_id | run.flowcell_id | Sequencer tracking |
| lane | run.lane | Multiplexing position |

### 11.4 Bidirectional Sync

- **LIMS -> NFDP:** Sample registration, library prep, sequencing completion trigger automatic record creation
- **NFDP -> LIMS:** QC results, validation status, ENA accessions pushed back to LIMS
- **Conflict resolution:** LIMS is source of truth for lab metadata; NFDP is source of truth for genomic data and accessions

---

## 12. ENA Public Submission Pathway

### 12.1 Phased Approach

**Phase 1 (MVP) — Manual Export**

```
System generates:
  +-- study.xml
  +-- sample.xml
  +-- experiment.xml
  +-- run.xml
  +-- submission.xml

Admin downloads --> Uploads via ENA Webin portal
                --> Enters ENA accessions back into system
```

**Phase 2 — Semi-automated**

- System generates XML + validates against ENA XSD schemas
- Admin reviews in portal, clicks "Submit to ENA"
- System uploads via Webin REST API (test server first)
- Accessions auto-imported

**Phase 3 — Fully automated**

- Programmatic submission via ENA REST API
- Auto-receive accessions and update records
- Support HOLD (embargo) and RELEASE actions
- Error handling with retry + admin notification

### 12.2 ENA Object Mapping

| Internal Entity | ENA Object | Accession Format |
|----------------|------------|-----------------|
| Study | Project | PRJEB______ |
| Sample | Sample | ERS________ |
| Experiment | Experiment | ERX________ |
| Run | Run | ERR________ |

---

## 13. Extensibility

The system is designed to grow with the facility. Each extension point is independent and does not require changes to the core.

### 13.1 New Data Types

Adding a new data type (e.g., proteomics, metabolomics, single-cell):

1. **Create a new checklist** — add a JSON schema to `/checklists/` defining required/optional fields
2. **Register the platform** — add to the `platform` enum in the Experiment model
3. **Add QC worker** — implement a new QC handler class that follows the existing interface
4. **Add storage bucket** — create a new MinIO bucket with appropriate policies

No changes needed to: API routes, upload flow, submission workflow, or frontend wizard (fields render dynamically from checklist).

### 13.2 New Organisms

Adding a new organism (e.g., falcon, fish):

1. Verify NCBI Taxonomy ID exists
2. Select or create appropriate ENA checklist
3. Add to SNP chip catalog if genotyping arrays exist
4. Add reference genome to the reference registry

No code changes required.

### 13.3 New Pipelines

Adding a new analysis pipeline:

1. Write a Nextflow script in `pipelines/`
2. Register in the pipeline registry (name, version, input types, parameters)
3. The pipeline becomes available in the admin panel for manual or automated triggering

### 13.4 New Integrations

| Integration | Method | Extension Point |
|-------------|--------|-----------------|
| New LIMS system | Implement webhook adapter | `/integrations/lims/` adapter interface |
| New public repository (DDBJ, NCBI) | Implement submission adapter | `/integrations/repositories/` adapter interface |
| External QC service | Implement QC handler | `/workers/qc/` handler interface |
| Notification channel (Teams, SMS) | Implement notifier | `/notifications/` notifier interface |

### 13.5 Plugin Architecture

```
nfdp/
  plugins/
    +-- checklists/          # Drop-in JSON schema files
    +-- qc_handlers/         # Drop-in QC worker classes
    +-- pipelines/           # Drop-in Nextflow scripts
    +-- integrations/        # Drop-in adapter classes
    +-- exporters/           # Drop-in format exporters (XML, JSON-LD, CSV)
```

Each plugin type follows a simple interface contract. New capabilities are added by dropping files into the appropriate directory — no core code modification needed.

### 13.6 API Versioning

- API versioned via URL path (`/api/v1/`, `/api/v2/`)
- Breaking changes only in new major versions
- Old versions supported for minimum 12 months after deprecation notice
- OpenAPI spec auto-generated and published at `/api/v1/docs`

---

## 14. Deployment Strategy

### 14.1 Development (Local)

All services run on a single machine via Docker Compose:

```yaml
services:
  frontend:    # Next.js on port 3000
  backend:     # FastAPI on port 8000
  postgres:    # PostgreSQL on port 5432
  minio:       # MinIO on port 9000 (console: 9001)
  redis:       # Redis on port 6379
  worker:      # QC/validation worker
```

### 14.2 Production (Hybrid Cloud)

**Cloud (portal + API):**
- Next.js on Vercel or containerized
- FastAPI on cloud VM or container service
- PostgreSQL managed instance (Cloud SQL, RDS, or equivalent)
- Redis managed instance

**On-prem (data + compute):**
- MinIO cluster on dedicated storage servers
- Nextflow + worker nodes on compute servers
- VPN tunnel to cloud layer

### 14.3 Monitoring

- Application metrics: Prometheus + Grafana
- Storage metrics: MinIO dashboard
- Pipeline monitoring: Nextflow Tower (optional)
- Uptime monitoring: health check endpoints

---

*This blueprint is a living document. It will be updated as the system evolves and new requirements emerge.*
