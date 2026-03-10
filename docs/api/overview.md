# API Overview

SeqDB provides a REST API modeled after the [ENA Portal API](https://www.ebi.ac.uk/ena/portal/api/). All responses are JSON.

## Base URL

| Environment | URL |
|-------------|-----|
| Local dev | `http://localhost:8000/api/v1` |
| Production | `https://api.seqdb.nfdp.dev/api/v1` |

## Interactive documentation

The backend automatically generates interactive API docs:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

## Authentication

Read-only endpoints (GET) are public. Write operations require a JWT Bearer token.

```bash
# Get a token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Use the token
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/projects/
```

See [Authentication](authentication.md) for details.

## Endpoints at a glance

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/register` | POST | No | Create account |
| `/auth/login` | POST | No | Get JWT token |
| `/projects/` | GET | No | List projects |
| `/projects/` | POST | Yes | Create project |
| `/projects/{acc}` | GET | No | Get project details |
| `/projects/{acc}` | PUT | Yes | Update project |
| `/projects/{acc}` | DELETE | Yes | Delete empty project |
| `/projects/{acc}/fair` | GET | No | Get FAIR score |
| `/samples/` | GET | No | List samples |
| `/samples/` | POST | Yes | Create sample |
| `/samples/{acc}` | GET | No | Get sample |
| `/experiments/` | GET | No | List experiments |
| `/experiments/` | POST | Yes | Create experiment |
| `/runs/` | GET | No | List runs |
| `/runs/{acc}` | GET | No | Get run |
| `/runs/{acc}/download` | GET | No | Download file (presigned URL) |
| `/runs/{acc}/qc` | GET | No | Get QC report |
| `/filereport` | GET | No | ENA-style file report |
| `/search/` | GET | No | Full-text search |
| `/staging/upload` | POST | Yes | Upload file to staging |
| `/staging/files` | GET | Yes | List staged files |
| `/bulk-submit/template/{id}` | GET | No | Download sample sheet template |
| `/bulk-submit/validate` | POST | Yes | Validate sample sheet |
| `/bulk-submit/confirm` | POST | Yes | Confirm bulk submission |
| `/checklists/` | GET | No | List checklists |
| `/checklists/{id}/schema` | GET | No | Get checklist schema |

## Accession format

All entities receive a persistent internal accession:

| Type | Format | Example |
|------|--------|---------|
| Project | `NFDP-PRJ-NNNNNN` | `NFDP-PRJ-000001` |
| Sample | `NFDP-SAM-NNNNNN` | `NFDP-SAM-000042` |
| Experiment | `NFDP-EXP-NNNNNN` | `NFDP-EXP-000007` |
| Run | `NFDP-RUN-NNNNNN` | `NFDP-RUN-000015` |

## Comparison with ENA API

```bash
# ENA — get files for a study
curl 'https://www.ebi.ac.uk/ena/portal/api/filereport?accession=PRJNA123&result=read_run&fields=run_accession,fastq_ftp,fastq_md5'

# SeqDB — equivalent
curl 'http://localhost:8000/api/v1/filereport?accession=NFDP-PRJ-000001'
```

| Feature | ENA API | SeqDB API |
|---------|---------|-----------|
| Base URL | `https://www.ebi.ac.uk/ena/portal/api` | `http://localhost:8000/api/v1` |
| File report | `filereport?accession=...&result=read_run` | `filereport?accession=...` |
| Response format | TSV (default) or JSON | JSON |
| Authentication | None (public data) | JWT for writes, public reads |
| Rate limit | 50 req/sec | None (current) |
| Download | FTP / Aspera URLs | Presigned URL redirect |

## Error handling

Errors return standard HTTP status codes with a JSON body:

```json
{
  "detail": "Project not found"
}
```

| Code | Meaning |
|------|---------|
| 400 | Bad request / validation error |
| 401 | Not authenticated |
| 403 | Not authorized (not owner) |
| 404 | Resource not found |
| 422 | Validation error (Pydantic) |

## Pagination

List endpoints support pagination:

```bash
curl 'http://localhost:8000/api/v1/samples/?page=2&per_page=50'
```

Default: `page=1`, `per_page=20`.
