# Samples API

Samples represent biological specimens with metadata (organism, collection info, etc.).

## List samples

```
GET /api/v1/samples/?project_accession={accession}&page=1&per_page=20
```

```bash
# All samples
curl 'http://localhost:8000/api/v1/samples/'

# Samples for a specific project
curl 'http://localhost:8000/api/v1/samples/?project_accession=NFDP-PRJ-000001'
```

**Response:**
```json
[
  {
    "accession": "NFDP-SAM-000001",
    "ena_accession": null,
    "organism": "Camelus dromedarius",
    "tax_id": 9838,
    "breed": "Arabian",
    "collection_date": "2026-01-15",
    "geographic_location": "Saudi Arabia:Riyadh",
    "checklist_id": "ERC000011",
    "created_at": "2026-01-15T10:30:00"
  }
]
```

## Get sample

```
GET /api/v1/samples/{accession}
```

```bash
curl 'http://localhost:8000/api/v1/samples/NFDP-SAM-000001'
```

## Create sample

```
POST /api/v1/samples/
```

Requires authentication.

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
    "host": "Camelus dromedarius",
    "tissue": "blood",
    "sex": "female"
  }'
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_accession` | string | Yes | Parent project accession |
| `checklist_id` | string | Yes | Metadata checklist ID |
| `organism` | string | Yes | Species name |
| `tax_id` | integer | Yes | NCBI taxonomy ID |
| `collection_date` | string | No | ISO date (YYYY-MM-DD) |
| `geographic_location` | string | No | Location (country:region) |
| `breed` | string | No | Animal breed |
| `host` | string | No | Host organism |
| `tissue` | string | No | Tissue type |
| `developmental_stage` | string | No | e.g., adult, juvenile |
| `sex` | string | No | male, female, unknown |

## Bulk create

For submitting many samples at once, use the [Bulk Submit API](bulk-submit.md) instead.

## Get files for a sample

Use the [File Report API](file-reports.md) with a sample accession:

```bash
curl 'http://localhost:8000/api/v1/filereport?accession=NFDP-SAM-000001'
```
