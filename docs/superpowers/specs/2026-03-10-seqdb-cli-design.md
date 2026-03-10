# SeqDB CLI Design Spec

**Date:** 2026-03-10
**Status:** Approved

## Overview

`seqdb-cli` is a Python CLI tool for interacting with the SeqDB genomic data platform. It provides two-way data flow: submitting sequencing data (like ENA Webin-CLI) and fetching reads with nf-core-compatible samplesheets (like nf-core/fetchngs for SRA). It also supports ingesting pipeline results (MultiQC) back into SeqDB.

## Command Surface

```
# Auth
seqdb login                                  # authenticate, store token
seqdb logout                                 # clear stored token

# Submit side (data in)
seqdb template <checklist_id>                # download TSV template
seqdb upload <files...>                      # stage files to SeqDB
seqdb validate <sample_sheet.tsv>            # validate sheet against API
seqdb submit <sample_sheet.tsv> [--files .]  # upload + validate + confirm (interactive gate)

# Fetch side (data out)
seqdb fetch <accession> [-o ./outdir]        # download reads + generate samplesheet
seqdb fetch <accession> --urls-only          # samplesheet with presigned URLs (no download)
seqdb fetch <accession> --format sarek       # nf-core pipeline-specific samplesheet

# Ingest side (results back in)
seqdb ingest <accession> --multiqc <path>    # attach QC results to a run/project

# Utility
seqdb status [accession]                     # check submission/project status
seqdb search <query>                         # search samples/projects
```

## Architecture

### Package: `seqdb-cli`

- **Framework:** Typer (modern Click wrapper)
- **HTTP client:** httpx (async)
- **Progress:** Rich (progress bars, tables)
- **Config:** `~/.seqdb/config.toml` (server URL, cached JWT)
- **Install:** `pip install seqdb-cli`

### Package Structure

```
cli/
├── pyproject.toml
├── src/seqdb_cli/
│   ├── __init__.py
│   ├── main.py                 # Typer app, register command groups
│   ├── config.py               # ~/.seqdb/config.toml management
│   ├── client.py               # httpx async client, auth headers, token refresh
│   ├── commands/
│   │   ├── auth.py             # login, logout
│   │   ├── submit.py           # template, upload, validate, submit
│   │   ├── fetch.py            # fetch with format mapping
│   │   ├── ingest.py           # multiqc ingestion
│   │   └── status.py           # status, search
│   ├── formats/
│   │   ├── __init__.py
│   │   ├── generic.py
│   │   ├── rnaseq.py
│   │   └── sarek.py
│   ├── transfer.py             # parallel upload/download with progress bars
│   └── utils.py                # MD5 computation, file discovery
├── tests/
│   ├── test_auth.py
│   ├── test_submit.py
│   ├── test_fetch.py
│   └── test_formats.py
```

## Data Flows

### Submit Flow (`seqdb submit sheet.tsv --files ./reads/`)

1. Discover files in `./reads/` (glob `*.fastq.gz`, `*.bam`, `*.cram`)
2. Compute MD5 locally (with progress bar)
3. `POST /api/v1/staging/initiate` per file → get presigned URLs
4. PUT files to MinIO via presigned URLs (parallel, with progress)
5. `POST /api/v1/staging/complete` per file → verify checksums
6. `POST /api/v1/bulk-submit/validate` with sheet.tsv
7. Print validation report (table: green/yellow/red per row)
8. Prompt: "Create N samples, N experiments, N runs? [y/N]"
9. `POST /api/v1/bulk-submit/confirm` → print created accessions

### Fetch Flow (`seqdb fetch NFDP-PRJ-000001 -o ./data/`)

1. `GET /api/v1/projects/{accession}` → project metadata
2. `GET /api/v1/samples?project={accession}` → list samples
3. For each sample → GET experiments → GET runs
4. For each run → `GET /api/v1/runs/{accession}/download` → presigned URL
5. Download files in parallel (with progress bar) to `./data/reads/`
6. Generate `samplesheet.csv` in chosen `--format`
7. Print: `Ready. Run: nextflow run nf-core/rnaseq --input ./data/samplesheet.csv`

### Fetch with `--urls-only`

Same as above but skip step 5. Samplesheet `fastq_1`/`fastq_2` columns contain presigned URLs instead of local paths.

### Ingest Flow (`seqdb ingest NFDP-PRJ-000001 --multiqc ./results/multiqc_data/`)

1. Parse `multiqc_data.json` for per-sample QC metrics
2. Match sample names to SeqDB run accessions
3. Upload QC report to MinIO via staging
4. Create QC report records via API

## nf-core Samplesheet Formats

### `generic` (default)

```csv
sample,fastq_1,fastq_2
NFDP-SAM-000001,/data/reads/sample001_R1.fastq.gz,/data/reads/sample001_R2.fastq.gz
```

### `rnaseq`

```csv
sample,fastq_1,fastq_2,strandedness
NFDP-SAM-000001,/data/reads/sample001_R1.fastq.gz,/data/reads/sample001_R2.fastq.gz,auto
```

### `sarek`

```csv
patient,sample,lane,fastq_1,fastq_2
organism_001,NFDP-SAM-000001,lane_1,/data/reads/sample001_R1.fastq.gz,/data/reads/sample001_R2.fastq.gz
```

### Column Mapping

| nf-core column | SeqDB source |
|---|---|
| `sample` | `internal_accession` or `external_id` |
| `fastq_1` | run forward read file path or presigned URL |
| `fastq_2` | run reverse read file path (empty for single-end) |
| `strandedness` | defaults to `auto`, overridable via `--strandedness` |
| `patient` | sample `organism` or `external_id` |
| `lane` | derived from run metadata or defaults to `lane_1` |

## Transfer

- `httpx.AsyncClient` with semaphore (default 4 concurrent)
- `--threads N` flag to control concurrency
- Rich progress bars per file + overall progress

## Authentication

- `seqdb login` → `POST /api/v1/auth/login` → store JWT in `~/.seqdb/config.toml`
- Auto-refresh token on 401
- All commands inject `Authorization: Bearer` header

## Scope

### In scope (launch)
- Auth (login/logout)
- Submit pipeline (template, upload, validate, submit)
- Fetch with generic/rnaseq/sarek formats
- `--urls-only` mode for presigned URL samplesheets
- MultiQC ingestion
- Status and search commands
- Documentation: user guide, CLI quickstart, API docs update

### Out of scope (future)
- Additional nf-core formats (eager, chipseq, etc.)
- FTP/SFTP upload from CLI
- Automated ENA submission relay
- Shell completions
