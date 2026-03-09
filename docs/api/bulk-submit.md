# Bulk Submit API

Submit many samples at once using a TSV sample sheet.

## Workflow

```
1. Download template  →  GET  /bulk-submit/template/{checklist_id}
2. Upload files       →  POST /staging/upload
3. Validate sheet     →  POST /bulk-submit/validate
4. Confirm            →  POST /bulk-submit/confirm
```

## Download template

```
GET /api/v1/bulk-submit/template/{checklist_id}
```

Returns a TSV file with all checklist columns plus file matching columns. Includes 2 demo rows with realistic example data.

```bash
curl -O 'http://localhost:8000/api/v1/bulk-submit/template/ERC000011'
```

Available checklists: `ERC000011`, `ERC000020`, `ERC000043`, `ERC000055`, `snpchip_livestock`

## Validate sample sheet

```
POST /api/v1/bulk-submit/validate
```

Requires authentication. Upload a filled TSV sheet for validation.

```bash
curl -X POST http://localhost:8000/api/v1/bulk-submit/validate \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@filled_template.tsv" \
  -F "checklist_id=ERC000011"
```

**Response:**

```json
{
  "valid": true,
  "total_rows": 2,
  "headers": ["sample_alias", "organism", "tax_id", "collection_date", ...],
  "required_fields": ["organism", "tax_id", "sample_alias"],
  "rows": [
    {
      "row_num": 2,
      "sample_alias": "SAMPLE_001",
      "cells": {
        "sample_alias": {"value": "SAMPLE_001", "status": "ok"},
        "organism": {"value": "Camelus dromedarius", "status": "ok"},
        "collection_date": {"value": "", "status": "empty_optional"}
      },
      "forward_file": {"filename": "SAMPLE_001_R1.fastq.gz", "md5": "abc123..."},
      "reverse_file": {"filename": "SAMPLE_001_R2.fastq.gz", "md5": "def456..."},
      "errors": [],
      "warnings": []
    }
  ],
  "errors": []
}
```

### Cell statuses

| Status | Meaning | Display |
|--------|---------|---------|
| `ok` | Field is filled and valid | Green |
| `empty_optional` | Optional field is empty | Yellow |
| `missing_required` | Required field is missing | Red |

## Confirm submission

```
POST /api/v1/bulk-submit/confirm
```

Requires authentication. Re-validates and creates all entities.

```bash
curl -X POST http://localhost:8000/api/v1/bulk-submit/confirm \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@filled_template.tsv" \
  -F "project_accession=NFDP-PRJ-000001" \
  -F "checklist_id=ERC000011"
```

**Response (success):**

```json
{
  "status": "created",
  "samples": ["NFDP-SAM-000002", "NFDP-SAM-000003"],
  "experiments": ["NFDP-EXP-000002", "NFDP-EXP-000003"],
  "runs": ["NFDP-RUN-000003", "NFDP-RUN-000004", "NFDP-RUN-000005", "NFDP-RUN-000006"]
}
```

**Response (validation failure):**

```json
{
  "detail": {
    "message": "Validation failed",
    "report": { ... }
  }
}
```

## What gets created

For each valid row in the sample sheet:

| Entity | Created from |
|--------|-------------|
| **Sample** | `sample_alias`, `organism`, `tax_id`, `collection_date`, etc. |
| **Experiment** | `platform`, `instrument_model`, `library_strategy`, `library_layout` |
| **Run** (forward) | `filename_forward` match → file path, checksum, size |
| **Run** (reverse) | `filename_reverse` match → file path, checksum, size |

## File matching

The system matches sample sheet rows to staged files using a 3-tier fallback:

1. **Exact filename** — `filename_forward` matches a staged file exactly
2. **MD5 checksum** — `md5_forward` matches a staged file's MD5
3. **Alias pattern** — `{sample_alias}[._-]R1` pattern in staged filenames

If no match is found, the error includes a "Did you mean...?" suggestion.
