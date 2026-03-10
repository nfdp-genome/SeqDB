# Projects API

Projects group related samples under a single study, similar to an ENA Study.

## List projects

```
GET /api/v1/projects/?page=1&per_page=20
```

```bash
curl 'http://localhost:8000/api/v1/projects/'
```

**Response:**
```json
[
  {
    "accession": "NFDP-PRJ-000001",
    "ena_accession": null,
    "title": "Arabian Camel WGS 2026",
    "description": "Whole genome sequencing study",
    "project_type": "WGS",
    "release_date": "2026-06-01",
    "license": "CC-BY",
    "created_at": "2026-01-15T10:00:00"
  }
]
```

## Get project

```
GET /api/v1/projects/{accession}
```

```bash
curl 'http://localhost:8000/api/v1/projects/NFDP-PRJ-000001'
```

## Create project

```
POST /api/v1/projects/
```

Requires authentication.

```bash
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Arabian Camel WGS 2026",
    "description": "Whole genome sequencing of Arabian camels in Riyadh",
    "project_type": "WGS"
  }'
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Project title |
| `description` | string | No | Detailed description |
| `project_type` | string | Yes | One of: `WGS`, `Metagenomics`, `Genotyping`, `Transcriptomics`, `Amplicon`, `Other` |
| `release_date` | string | No | ISO date (YYYY-MM-DD) |
| `license` | string | No | Default: `CC-BY` |

## Update project

```
PUT /api/v1/projects/{accession}
```

Requires authentication. Only the project owner can update.

```bash
curl -X PUT http://localhost:8000/api/v1/projects/NFDP-PRJ-000001 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Title",
    "description": "Updated description",
    "release_date": "2026-06-01",
    "license": "CC-BY-SA"
  }'
```

## Delete project

```
DELETE /api/v1/projects/{accession}
```

Requires authentication. Only works on **empty projects** (no samples).

```bash
curl -X DELETE http://localhost:8000/api/v1/projects/NFDP-PRJ-000001 \
  -H "Authorization: Bearer $TOKEN"
```

## FAIR score

```
GET /api/v1/projects/{accession}/fair
```

Returns per-project FAIR compliance scores.

```bash
curl 'http://localhost:8000/api/v1/projects/NFDP-PRJ-000001/fair'
```

See [FAIR Data Principles](../user-guide/fair-data.md) for details on scoring.
