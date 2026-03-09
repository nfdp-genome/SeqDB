# SeqDB

**SeqDB** is a web-based genomic data deposition and management platform for submitting, managing, and sharing sequencing data. It follows the [ENA (European Nucleotide Archive)](https://www.ebi.ac.uk/ena/) data model and provides an ENA-compatible API for programmatic access. Designed for NFDP genome and data science Dept at NFDP.
---

## What is SeqDB?

SeqDB is a genomic data repository designed for:

- **Sequencing facilities** depositing raw reads (FASTQ, BAM, CRAM)
- **Researchers** submitting sample metadata with standardized checklists
- **Bioinformaticians** downloading data programmatically via REST API
- **Data managers** ensuring FAIR compliance and ENA interoperability

## Key Features

| Feature                  | Description                                                      |
|--------------------------|------------------------------------------------------------------|
| **ENA-style data model** | Project → Sample → Experiment → Run hierarchy                    |
| **Bulk submission**      | Upload TSV sample sheets with automatic file matching            |
| **File staging**         | Upload files via browser or FTP before linking to samples        |
| **FAIR scoring**         | Per-project Findable, Accessible, Interoperable, Reusable checks |
| **Programmatic API**     | ENA-compatible `/filereport` endpoint with download URLs         |
| **Metadata validation**  | Checklist-based validation with cell-level error highlighting    |
| **Presigned downloads**  | Secure, time-limited download URLs for all files                 |

## Data Model

The platform follows the ENA submission hierarchy:

```
Project (NFDP-PRJ-*)        ← Study-level metadata
  └── Sample (NFDP-SAM-*)       ← Organism, collection info
       └── Experiment (NFDP-EXP-*)  ← Sequencing platform, library
            └── Run (NFDP-RUN-*)      ← File, checksum, download
```

## Quick Links

- [Quick Start](user-guide/quickstart.md) — Get up and running in 5 minutes
- [API Overview](api/overview.md) — Programmatic access guide
- [File Reports](api/file-reports.md) — ENA-style file download API
- [Bulk Submission](user-guide/bulk-submission.md) — Submit many samples at once
- [Cloud Deployment](architecture/cloud-deployment.md) — Production deployment guide

## Comparison with ENA

| Concept              | ENA                                                            | SeqDB                                                  |
|----------------------|----------------------------------------------------------------|--------------------------------------------------------|
| File report endpoint | `GET /ena/portal/api/filereport?accession=...&result=read_run` | `GET /api/v1/filereport?accession=...`                 |
| Accession format     | `ERR`, `ERS`, `ERX`, `ERP`                                     | `NFDP-RUN-*`, `NFDP-SAM-*`, `NFDP-EXP-*`, `NFDP-PRJ-*` |
| Metadata checklists  | ERC000011, ERC000020, etc.                                     | Same checklist IDs                                     |
| Bulk submission      | Webin spreadsheet upload                                       | TSV sample sheet upload                                |
| File download        | FTP / Aspera                                                   | Presigned URLs (S3-compatible)                         |
| Response format      | TSV (default)                                                  | JSON                                                   |

---

!!! info "Under Development"
    This platform is actively developed by the SeqDB team. For questions or contributions, see the [Developer Guide](developer/contributing.md).
