# ENA-Style Bulk Submit — Design Document

**Date:** 2026-03-08
**Status:** Approved

## Goal

Add an ENA-style bulk submission workflow alongside the existing quick submit wizard. Researchers upload files to a staging area (browser or FTP), then upload a single sample sheet (TSV) that contains metadata and file linkage info. The system validates checksums, matches files to samples, and creates all entities atomically.

## Data Model Changes

### Rename Study to Project

- Rename `studies` table to `projects` throughout the codebase
- Model, schema, API endpoints, accession type, all references
- Accession prefix stays `NFDP-PRJ-`
- Migration: rename table + update foreign keys

### New Table: `staged_files`

| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| user_id | FK → users.id | Owner |
| filename | String(500) | Original filename |
| file_size | BigInteger | Bytes |
| checksum_md5 | String(32) | Computed server-side |
| upload_method | Enum(browser, ftp) | How the file arrived |
| staging_path | String(1000) | MinIO path in staging bucket |
| status | Enum(pending, verified, linked, expired) | Lifecycle state |
| uploaded_at | DateTime | |
| expires_at | DateTime | Auto-cleanup after 7 days |

## Two Submission Modes

### Mode 1: Quick Submit (existing wizard, renamed)

- Single sample, single experiment, inline file upload
- Project → Sample → Experiment → Upload → Review
- Good for: one-off submissions, small datasets
- Only change: rename Study → Project in UI labels

### Mode 2: Bulk Submit (new ENA-style flow)

```
1. Create/Select Project           → NFDP-PRJ-XXXXXX
2. Upload files to staging         → nfdp-staging/{user_id}/
3. Upload sample sheet (TSV)       → validates metadata + links files
4. System validates checksums + metadata + file matching
5. Auto-creates Samples, Experiments, Runs in batch
6. Review accessions & release
```

## Upload Methods (Step 2)

### Method A: Browser Upload (drag-and-drop)

- Presigned PUT URLs directly to MinIO staging bucket
- Frontend computes MD5 via Web Crypto API during upload
- Good for smaller files or quick uploads

### Method B: FTP/SFTP Upload

- Dedicated FTP/SFTP endpoint (vsftpd or similar)
- Virtual users mapped to portal accounts
- Incoming directory: `/data/ftp-incoming/{user_id}/`
- Background FileWatcher service:
  - Polls FTP directory for new files
  - Computes MD5
  - Moves files to MinIO staging (`nfdp-staging/{user_id}/`)
  - Inserts record into `staged_files` table
- Good for large files (multi-GB FASTQ) or automated pipelines

### Method C: CLI Upload (future phase)

- CLI tool similar to ENA's Webin-CLI
- Uploads files + optionally submits sample sheet in one command
- Deferred to future implementation

All methods land files in the same MinIO staging bucket. The sample sheet validation does not care how files arrived.

## Sample Sheet Format

Single TSV file combining metadata and file linkage.

### Required columns (from checklist)

- sample_alias (user-defined unique identifier per sample)
- organism
- tax_id
- collection_date
- geographic_location
- Additional fields per selected checklist

### Optional file linkage columns

- filename_forward
- filename_reverse
- md5_forward
- md5_reverse
- library_strategy
- library_source
- library_layout
- platform
- instrument_model
- insert_size

### File matching logic

1. If `filename_forward`/`filename_reverse` columns present: use explicit filenames
2. Otherwise, auto-detect by naming convention: `{sample_alias}_R1.fastq.gz` / `{sample_alias}_R2.fastq.gz`
3. MD5 validation: server-side MD5 of staged file must match declared `md5_forward`/`md5_reverse`

## Validation Pipeline (Step 3-4)

When user uploads the sample sheet, backend validates in order:

1. **Schema validation** — required fields present, types correct (per checklist)
2. **File matching** — for each row, find staged files by naming convention OR explicit filenames
3. **MD5 verification** — server-computed MD5 of staged file matches declared checksum
4. Returns a validation report:
   - Green: all rows pass
   - Yellow: warnings (optional fields missing)
   - Red: errors with row number, field name, message

### Error cases

- MD5 mismatch: "File X checksum mismatch: expected abc..., got def... Re-upload the file."
- Missing file: "No staged file found for sample SAMPLE01. Upload it or specify filename explicitly."
- Validation error: row-level errors with field name and message
- Partial failure: nothing is created; user fixes issues and resubmits

## Confirm & Create (Step 5)

On user confirmation:

1. Atomically create: Samples → Experiments → Runs (one transaction)
2. Move files from `nfdp-staging/{user_id}/` → `nfdp-raw/{project}/{sample}/{run}/`
3. Update `staged_files.status` → `linked`
4. Return all accessions

## MinIO Bucket Structure

- `nfdp-staging/{user_id}/` — temporary upload area (auto-cleanup after 7 days)
- `nfdp-raw/{project}/{sample}/{run}/` — permanent archive after linking
- `nfdp-qc/` — QC reports (unchanged)
- `nfdp-processed/` — processed data (unchanged)

## New API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /staging/initiate | Get presigned URL for browser upload to staging |
| GET | /staging/files | List current user's staged files |
| DELETE | /staging/files/{id} | Remove a staged file |
| POST | /bulk-submit/validate | Validate sample sheet against staged files |
| POST | /bulk-submit/confirm | Create all entities + move files to archive |
| GET | /bulk-submit/template/{checklist_id} | Download bulk sample sheet template |

## New Backend Services

- **StagingService** — manage staged files, presigned URLs, MD5 verification, expiry cleanup
- **BulkSubmitService** — parse sample sheet, match files, validate, create entities atomically
- **FTPWatcherService** — background worker monitoring FTP incoming directory, moves to MinIO

## Frontend Changes

### `/submit` page — mode selector

Two cards: "Quick Submit" (existing wizard) and "Bulk Submit" (new flow).

### Bulk Submit UI (new pages/components)

1. **Project step** — create new or select existing project
2. **Upload step** — drag-and-drop zone + staged files table + FTP instructions panel showing connection details
3. **Sample sheet step** — select checklist, download template, upload filled TSV, view validation report (green/yellow/red)
4. **Confirm step** — review table of all entities to be created (samples, experiments, runs), confirm button, accession summary on completion

### Quick Submit (existing wizard)

- Rename Study → Project in labels
- No other changes

## What Stays The Same

- Checklist system and JSON schema validation
- Template generation service
- MinIO archive bucket structure (nfdp-raw/)
- Authentication (JWT)
- QC reports
- Submission/validation endpoints
- Browse, FAIR dashboard, admin pages
