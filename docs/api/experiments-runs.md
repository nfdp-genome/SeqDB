# Experiments & Runs API

**Experiments** describe how a sample was sequenced (platform, library info).
**Runs** represent individual data files with checksums and download URLs.

## Experiments

### List experiments

```bash
curl 'http://localhost:8000/api/v1/experiments/?page=1&per_page=20'
```

### Get experiment

```bash
curl 'http://localhost:8000/api/v1/experiments/NFDP-EXP-000001'
```

### Create experiment

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
    "library_layout": "PAIRED",
    "insert_size": 350
  }'
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sample_accession` | string | Yes | Parent sample accession |
| `platform` | string | Yes | `ILLUMINA`, `OXFORD_NANOPORE`, `PACBIO_SMRT`, etc. |
| `instrument_model` | string | Yes | e.g., `Illumina NovaSeq 6000` |
| `library_strategy` | string | Yes | `WGS`, `WXS`, `RNA-Seq`, `AMPLICON`, etc. |
| `library_source` | string | Yes | `GENOMIC`, `TRANSCRIPTOMIC`, `METAGENOMIC`, etc. |
| `library_layout` | string | Yes | `PAIRED` or `SINGLE` |
| `insert_size` | integer | No | Insert size in bp |

!!! note
    In bulk submission, experiments are created automatically from the sample sheet columns (`platform`, `instrument_model`, `library_strategy`).

---

## Runs

### List runs

```bash
curl 'http://localhost:8000/api/v1/runs/?page=1&per_page=20'
```

**Response:**
```json
[
  {
    "accession": "NFDP-RUN-000001",
    "ena_accession": null,
    "file_type": "FASTQ",
    "file_size": 1234567890,
    "checksum_md5": "d41d8cd98f00b204e9800998ecf8427e",
    "created_at": "2026-01-15T10:30:00"
  }
]
```

### Get run

```bash
curl 'http://localhost:8000/api/v1/runs/NFDP-RUN-000001'
```

### Download file

```
GET /api/v1/runs/{accession}/download
```

Returns a **307 redirect** to a presigned download URL (valid for 24 hours).

```bash
# Follow redirect and save file
curl -L -O 'http://localhost:8000/api/v1/runs/NFDP-RUN-000001/download'

# Get just the URL without downloading
curl -s 'http://localhost:8000/api/v1/runs/NFDP-RUN-000001/download' | head -1
```

!!! info "Dev mode"
    When MinIO is not available (local dev with SQLite), the download endpoint returns file metadata instead of redirecting:
    ```json
    {
      "accession": "NFDP-RUN-000001",
      "file_path": "SAMPLE_001_R1.fastq.gz",
      "file_size": 1234567890,
      "checksum_md5": "d41d8cd98f00b204e9800998ecf8427e",
      "message": "Direct download unavailable — file stored at the path above"
    }
    ```

### QC reports

```bash
curl 'http://localhost:8000/api/v1/runs/NFDP-RUN-000001/qc'
```

**Response:**
```json
{
  "status": "passed",
  "tool": "FastQC",
  "summary": {"total_sequences": 50000000, "gc_content": 42.5},
  "report_url": "/qc/NFDP-RUN-000001/fastqc_report.html",
  "reports": [
    {"tool": "FastQC", "status": "passed", "summary": {...}},
    {"tool": "MultiQC", "status": "passed", "summary": {...}}
  ]
}
```

If QC has not been run yet:
```json
{"status": "pending", "reports": []}
```

## Supported file types

| Type | Extensions |
|------|-----------|
| FASTQ | `.fastq`, `.fastq.gz`, `.fq`, `.fq.gz` |
| BAM | `.bam` |
| CRAM | `.cram` |
| VCF | `.vcf`, `.vcf.gz` |
