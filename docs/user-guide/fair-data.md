# FAIR Data Principles

The SeqDB platform includes built-in FAIR scoring to help you make your genomic data Findable, Accessible, Interoperable, and Reusable.

## What is FAIR?

[FAIR principles](https://www.go-fair.org/fair-principles/) ensure scientific data is machine-actionable and can be found, accessed, and reused by others.

| Principle | What it means |
|-----------|--------------|
| **Findable** | Data has persistent identifiers, rich metadata, and is registered in a searchable resource |
| **Accessible** | Data can be retrieved via standard protocols with clear access conditions |
| **Interoperable** | Data uses shared vocabularies and standard formats |
| **Reusable** | Data has clear licensing and provenance information |

## FAIR scoring in SeqDB

Each project has a FAIR score visible on its detail page. The score is computed from concrete checks:

### Findable checks

- Project has a title
- Project has a description
- Project has a release date
- Project has at least one sample
- Samples have geographic locations

### Accessible checks

- Files are downloadable via presigned URLs
- File checksums (MD5) are available
- API provides programmatic access

### Interoperable checks

- Samples use a standard checklist (ERC000011, etc.)
- NCBI taxonomy IDs are provided
- Standard file formats (FASTQ, BAM, CRAM, VCF)

### Reusable checks

- Project has a license (CC-BY, CC0, etc.)
- Collection dates are provided
- Sample metadata is complete (organism, breed, tissue, etc.)

## Viewing your FAIR score

### Web UI

Navigate to your project page. The FAIR score panel shows:

- Four dimension scores (0–100%)
- Actionable suggestions for improvement
- Entity counts (samples, experiments, runs)

### API

```bash
curl 'http://localhost:8000/api/v1/projects/NFDP-PRJ-000001/fair'
```

```json
{
  "scores": {
    "findable": 0.75,
    "accessible": 1.0,
    "interoperable": 0.5,
    "reusable": 0.8
  },
  "checks": {
    "findable": {"has_title": true, "has_description": true, "has_release_date": false},
    "accessible": {"files_downloadable": true, "checksums_available": true},
    "interoperable": {"uses_checklist": true, "has_taxonomy": true},
    "reusable": {"has_license": true, "has_collection_dates": false}
  },
  "suggestions": [
    "Add a release date to improve Findability",
    "Add collection dates to samples for better Reusability"
  ],
  "counts": {"samples": 5, "experiments": 5, "runs": 10}
}
```

## Improving your score

| Suggestion | How to fix |
|------------|-----------|
| Add a project description | Edit project → fill Description field |
| Set a release date | Edit project → set Release Date |
| Add a license | Edit project → select a license (CC-BY recommended) |
| Add collection dates | Include `collection_date` in your sample sheet |
| Add geographic locations | Include `geographic_location` in your sample sheet |
| Use a metadata checklist | Select an ENA checklist when submitting samples |
