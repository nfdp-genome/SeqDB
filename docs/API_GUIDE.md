# SeqDB Programmatic Access Guide

The SeqDB platform provides a REST API modeled after the [ENA Portal API](https://www.ebi.ac.uk/ena/portal/api/). If you have used ENA's programmatic access before, you will find this familiar.

**Base URL:** `http://localhost:8000/api/v1` (dev) or `https://nfdp.example.sa/api/v1` (production)

---

## Quick Comparison: ENA vs SeqDB

| Feature | ENA | SeqDB |
|---------|-----|-------|
| File report | `GET /ena/portal/api/filereport?accession=...&result=read_run` | `GET /api/v1/filereport?accession=...` |
| Search | `GET /ena/portal/api/search?query=...` | `GET /api/v1/search?q=...` |
| Download file | FTP/Aspera URLs in file report | `GET /api/v1/runs/{accession}/download` (presigned URL redirect) |
| Accession format | `ERR`, `ERS`, `ERX`, `ERP`, `PRJ` | `NFDP-RUN-*`, `NFDP-SAM-*`, `NFDP-EXP-*`, `NFDP-PRJ-*` |
| Auth | Public (no auth) | Bearer token (JWT) for write ops; read ops are public |
| Response format | TSV (default) or JSON | JSON |

---

## 1. Authentication

Read-only endpoints (GET) work without authentication. All write operations require a JWT token.

### Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "Ahmed Ali",
    "role": "researcher"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword"}'
```

Response:
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "expires_in": 3600
}
```

Use the token in subsequent requests:
```bash
curl -H "Authorization: Bearer eyJhbG..." http://localhost:8000/api/v1/projects/
```

---

## 2. File Reports (ENA-style)

The `/filereport` endpoint works like ENA's file report — query by any accession to get file metadata and download URLs.

### Endpoint

```
GET /api/v1/filereport?accession={accession}
```

### Accession Types

| Prefix | Type | Example |
|--------|------|---------|
| `NFDP-PRJ-` | Project (like ENA Study) | `NFDP-PRJ-000001` |
| `NFDP-SAM-` | Sample | `NFDP-SAM-000001` |
| `NFDP-EXP-` | Experiment | `NFDP-EXP-000001` |
| `NFDP-RUN-` | Run | `NFDP-RUN-000001` |

### Examples

**All files in a project** (like ENA: `filereport?accession=PRJNA123&result=read_run`):
```bash
curl 'http://localhost:8000/api/v1/filereport?accession=NFDP-PRJ-000001'
```

**Files for a specific sample:**
```bash
curl 'http://localhost:8000/api/v1/filereport?accession=NFDP-SAM-000001'
```

**Single run file info:**
```bash
curl 'http://localhost:8000/api/v1/filereport?accession=NFDP-RUN-000001'
```

### Response

```json
[
  {
    "run_accession": "NFDP-RUN-000001",
    "experiment_accession": "NFDP-EXP-000001",
    "sample_accession": "NFDP-SAM-000001",
    "project_accession": "NFDP-PRJ-000001",
    "organism": "Camelus dromedarius",
    "tax_id": 9838,
    "file_type": "FASTQ",
    "filename": "SAMPLE_001_R1.fastq.gz",
    "file_path": "nfdp-raw/NFDP-PRJ-000001/NFDP-SAM-000001/NFDP-RUN-000001/SAMPLE_001_R1.fastq.gz",
    "file_size": 1234567890,
    "checksum_md5": "d41d8cd98f00b204e9800998ecf8427e",
    "checksum_sha256": null,
    "download_url": "/api/v1/runs/NFDP-RUN-000001/download",
    "platform": "ILLUMINA",
    "instrument_model": "Illumina NovaSeq 6000",
    "library_strategy": "WGS",
    "library_layout": "PAIRED"
  }
]
```

### Comparison with ENA

```bash
# ENA — get all FASTQ files for a study
curl 'https://www.ebi.ac.uk/ena/portal/api/filereport?accession=PRJNA123456&result=read_run&fields=run_accession,fastq_ftp,fastq_md5,fastq_bytes'

# SeqDB — equivalent
curl 'http://localhost:8000/api/v1/filereport?accession=NFDP-PRJ-000001'
```

---

## 3. Downloading Files

### Direct download (presigned URL)

```bash
# Browser or curl — redirects (307) to a time-limited presigned URL
curl -L -O 'http://localhost:8000/api/v1/runs/NFDP-RUN-000001/download'
```

The download URL is valid for 24 hours. After expiry, request a new one.

### Batch download (scripted)

Use the file report to get all download URLs, then download in parallel:

```bash
# Get all file URLs for a project and download with wget
curl -s 'http://localhost:8000/api/v1/filereport?accession=NFDP-PRJ-000001' \
  | python3 -c "
import json, sys
files = json.load(sys.stdin)
for f in files:
    print(f['download_url'])
" | xargs -P 4 -I {} wget -q 'http://localhost:8000{}'
```

Or with `jq`:
```bash
curl -s 'http://localhost:8000/api/v1/filereport?accession=NFDP-PRJ-000001' \
  | jq -r '.[].download_url' \
  | while read url; do
      curl -L -O "http://localhost:8000${url}"
    done
```

### Verify checksums after download

```bash
# Get expected MD5s
curl -s 'http://localhost:8000/api/v1/filereport?accession=NFDP-PRJ-000001' \
  | jq -r '.[] | "\(.checksum_md5)  \(.filename)"' > expected_md5.txt

# Check downloaded files
md5sum -c expected_md5.txt
```

---

## 4. Projects

### Create a project

```bash
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Camel WGS Study 2026",
    "description": "Whole genome sequencing of Arabian camels",
    "project_type": "whole_genome_sequencing"
  }'
```

### List projects

```bash
curl 'http://localhost:8000/api/v1/projects/?page=1&per_page=50'
```

### Get project details

```bash
curl 'http://localhost:8000/api/v1/projects/NFDP-PRJ-000001'
```

### Get FAIR score

```bash
curl 'http://localhost:8000/api/v1/projects/NFDP-PRJ-000001/fair'
```

Response:
```json
{
  "scores": {"findable": 0.75, "accessible": 1.0, "interoperable": 0.5, "reusable": 0.8},
  "checks": { ... },
  "suggestions": ["Add a release date to improve Findability"],
  "counts": {"samples": 5, "experiments": 5, "runs": 10}
}
```

### Update a project

```bash
curl -X PUT http://localhost:8000/api/v1/projects/NFDP-PRJ-000001 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title", "license": "CC-BY"}'
```

### Delete a project (only if empty)

```bash
curl -X DELETE http://localhost:8000/api/v1/projects/NFDP-PRJ-000001 \
  -H "Authorization: Bearer $TOKEN"
```

---

## 5. Samples

### List samples for a project

```bash
curl 'http://localhost:8000/api/v1/samples/?project_accession=NFDP-PRJ-000001'
```

### Get a sample

```bash
curl 'http://localhost:8000/api/v1/samples/NFDP-SAM-000001'
```

### Create a sample

```bash
curl -X POST http://localhost:8000/api/v1/samples/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_accession": "NFDP-PRJ-000001",
    "checklist_id": "ERC000011",
    "organism": "Camelus dromedarius",
    "tax_id": 9838,
    "collection_date": "2026-01-15",
    "geographic_location": "Saudi Arabia:Riyadh",
    "breed": "Arabian",
    "sex": "female"
  }'
```

---

## 6. Experiments

### List experiments

```bash
curl 'http://localhost:8000/api/v1/experiments/'
```

### Create an experiment

```bash
curl -X POST http://localhost:8000/api/v1/experiments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sample_accession": "NFDP-SAM-000001",
    "platform": "ILLUMINA",
    "instrument_model": "Illumina NovaSeq 6000",
    "library_strategy": "WGS",
    "library_source": "GENOMIC",
    "library_layout": "PAIRED"
  }'
```

---

## 7. Runs & QC

### Get run details

```bash
curl 'http://localhost:8000/api/v1/runs/NFDP-RUN-000001'
```

### Get QC report for a run

```bash
curl 'http://localhost:8000/api/v1/runs/NFDP-RUN-000001/qc'
```

---

## 8. Bulk Submission

The bulk workflow mirrors submitting to ENA via spreadsheet.

### Step 1: Download template

```bash
curl -O 'http://localhost:8000/api/v1/bulk-submit/template/ERC000011'
# Produces: ERC000011_bulk_template.tsv with 2 demo rows
```

### Step 2: Fill the template

Edit the TSV file — replace demo rows with real sample metadata. Columns include:
- `sample_alias` — unique identifier per sample
- `organism`, `tax_id` — species info
- `collection_date`, `geographic_location` — when/where
- `filename_forward`, `filename_reverse` — FASTQ filenames (must match staged files)
- `md5_forward`, `md5_reverse` — checksums (optional, used for verification)
- `platform`, `instrument_model`, `library_strategy` — sequencing info

### Step 3: Upload files to staging

```bash
# Direct upload (recommended for files < 5GB)
curl -X POST http://localhost:8000/api/v1/staging/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@SAMPLE_001_R1.fastq.gz"
```

### Step 4: Validate the sample sheet

```bash
curl -X POST http://localhost:8000/api/v1/bulk-submit/validate \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@filled_template.tsv" \
  -F "checklist_id=ERC000011"
```

The response shows per-cell validation with statuses: `ok`, `missing_required`, `empty_optional`.

### Step 5: Confirm submission

```bash
curl -X POST http://localhost:8000/api/v1/bulk-submit/confirm \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@filled_template.tsv" \
  -F "project_accession=NFDP-PRJ-000001" \
  -F "checklist_id=ERC000011"
```

Response:
```json
{
  "status": "created",
  "samples": ["NFDP-SAM-000002", "NFDP-SAM-000003"],
  "experiments": ["NFDP-EXP-000002", "NFDP-EXP-000003"],
  "runs": ["NFDP-RUN-000003", "NFDP-RUN-000004", "NFDP-RUN-000005", "NFDP-RUN-000006"]
}
```

---

## 9. Search

### Full-text search across projects and samples

```bash
# Search for "camel"
curl 'http://localhost:8000/api/v1/search/?q=camel'

# Search only samples
curl 'http://localhost:8000/api/v1/search/?q=camel&type=sample'
```

---

## 10. File Staging

Staging is a temporary area for files before they are linked to runs via bulk submission.

### Upload a file to staging

```bash
curl -X POST http://localhost:8000/api/v1/staging/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@my_sample_R1.fastq.gz"
```

### List staged files

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/staging/files
```

### Delete a staged file

```bash
curl -X DELETE http://localhost:8000/api/v1/staging/files/42 \
  -H "Authorization: Bearer $TOKEN"
```

---

## 11. Checklists

Checklists define which metadata fields are required for samples (similar to ENA checklists).

### List available checklists

```bash
curl 'http://localhost:8000/api/v1/checklists/'
```

### Get checklist schema

```bash
curl 'http://localhost:8000/api/v1/checklists/ERC000011/schema'
```

---

## Data Model

```
Project (NFDP-PRJ-*)
  └── Sample (NFDP-SAM-*)         ← organism, collection info
       └── Experiment (NFDP-EXP-*)  ← platform, library info
            └── Run (NFDP-RUN-*)      ← file, checksum, download
```

This mirrors the ENA hierarchy: Study → Sample → Experiment → Run.

---

## Python Example

```python
import requests

BASE = "http://localhost:8000/api/v1"

# Login
token = requests.post(f"{BASE}/auth/login", json={
    "email": "user@example.com",
    "password": "password"
}).json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Get all files for a project
files = requests.get(f"{BASE}/filereport", params={
    "accession": "NFDP-PRJ-000001"
}).json()

# Download each file
for f in files:
    print(f"Downloading {f['filename']} ({f['file_size']} bytes)...")
    resp = requests.get(f"{BASE}{f['download_url']}", allow_redirects=True)
    with open(f['filename'], 'wb') as out:
        out.write(resp.content)
    print(f"  MD5: {f['checksum_md5']}")
```

---

## Rate Limits

No rate limits are enforced in the current version. For production, consider adding rate limiting similar to ENA's 50 requests/second policy.

## OpenAPI Docs

Interactive API documentation is available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
