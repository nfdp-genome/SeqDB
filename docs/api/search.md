# Search API

Full-text search across projects and samples.

## Endpoint

```
GET /api/v1/search/?q={query}&type={type}&page=1&per_page=20
```

No authentication required.

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `q` | Yes | — | Search query (minimum 1 character) |
| `type` | No | `project,sample` | Comma-separated entity types to search |
| `page` | No | 1 | Page number |
| `per_page` | No | 20 | Results per page |

## Examples

### Search for "camel"

```bash
curl 'http://localhost:8000/api/v1/search/?q=camel'
```

**Response:**
```json
{
  "query": "camel",
  "total": 3,
  "results": [
    {
      "type": "project",
      "accession": "NFDP-PRJ-000001",
      "title": "Arabian Camel WGS 2026",
      "description": "Whole genome sequencing study"
    },
    {
      "type": "sample",
      "accession": "NFDP-SAM-000001",
      "organism": "Camelus dromedarius",
      "breed": "Arabian",
      "geographic_location": "Saudi Arabia:Riyadh"
    }
  ]
}
```

### Search only samples

```bash
curl 'http://localhost:8000/api/v1/search/?q=dromedarius&type=sample'
```

### Search only projects

```bash
curl 'http://localhost:8000/api/v1/search/?q=WGS&type=project'
```
