# Checklists API

Checklists define which metadata fields are required for sample registration. They mirror ENA metadata checklists.

## List checklists

```
GET /api/v1/checklists/
```

```bash
curl 'http://localhost:8000/api/v1/checklists/'
```

**Response:**
```json
[
  {"id": "ERC000011", "name": "ENA Default"},
  {"id": "ERC000020", "name": "Pathogen Clinical/Host-associated"},
  {"id": "ERC000043", "name": "Virus Pathogen"},
  {"id": "ERC000055", "name": "Farm Animal"},
  {"id": "snpchip_livestock", "name": "SNP Chip Livestock"}
]
```

## Get checklist schema

```
GET /api/v1/checklists/{checklist_id}/schema
```

Returns a JSON Schema describing all fields, their types, and which are required.

```bash
curl 'http://localhost:8000/api/v1/checklists/ERC000011/schema'
```

**Response:**
```json
{
  "id": "ERC000011",
  "name": "ENA Default",
  "required": ["organism", "tax_id"],
  "properties": {
    "organism": {"type": "string", "description": "Species name"},
    "tax_id": {"type": "integer", "description": "NCBI taxonomy ID"},
    "collection_date": {"type": "string", "format": "date"},
    "geographic_location": {"type": "string"},
    "breed": {"type": "string"},
    "host": {"type": "string"},
    "tissue": {"type": "string"},
    "developmental_stage": {"type": "string"},
    "sex": {"type": "string", "enum": ["male", "female", "unknown"]}
  }
}
```

## Available checklists

| ID | Name | Required Fields | Use Case |
|----|------|----------------|----------|
| `ERC000011` | ENA Default | organism, tax_id | General-purpose genomic submissions |
| `ERC000020` | Pathogen Clinical/Host | organism, tax_id, isolation_source, host | Clinical pathogen samples |
| `ERC000043` | Virus Pathogen | organism, tax_id, strain, isolation_source | Viral genomics |
| `ERC000055` | Farm Animal | organism, tax_id, breed | Livestock breeding studies |
| `snpchip_livestock` | SNP Chip Livestock | organism, tax_id, breed | SNP genotyping arrays |

## How checklists are used

1. **Template generation** — `GET /bulk-submit/template/{checklist_id}` generates a TSV with all checklist fields as columns
2. **Validation** — `POST /bulk-submit/validate` checks required fields against the checklist
3. **Sample creation** — `POST /samples/` uses `checklist_id` to tag the sample
