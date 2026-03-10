# Quick Start

Get the SeqDB platform running locally in 5 minutes.

## Prerequisites

- Python 3.12+
- Node.js 20+
- Git

## 1. Clone and set up the backend

```bash
git clone https://github.com/nfdp-genome/SeqDB.git
cd SeqDB/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure local environment
cp ../.env.example ../.env
# Edit .env if needed — defaults use SQLite for dev
```

## 2. Start the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The API is now available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

!!! note "SQLite for local dev"
    By default, the backend uses SQLite (`dev.db`) for local development. Tables are created automatically on startup. For production, use PostgreSQL.

## 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

The web UI is now available at `http://localhost:3000`.

## 4. Create your first submission

### Via the Web UI

1. Open `http://localhost:3000`
2. Register an account (or use default dev credentials)
3. Click **Submit** → **Bulk Submit**
4. Create a new project
5. Upload sequencing files to the staging area
6. Download a sample sheet template, fill it in, and upload
7. Review validation results, then confirm

### Via the API

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123", "full_name": "Test User", "role": "submitter"}'

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Create project
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My First Study", "description": "Test project", "project_type": "WGS"}'
```

## CLI Quick Start

Install the CLI:

    pip install seqdb-cli

Login:

    seqdb login --url http://localhost:8000 --email you@example.com

Submit data:

    seqdb template ERC000011
    # Fill in template.tsv with your metadata
    seqdb submit template.tsv --checklist ERC000011 --project NFDP-PRJ-000001 --files ./reads/

Fetch reads for a pipeline:

    seqdb fetch NFDP-PRJ-000001 -o ./data/ --format rnaseq
    nextflow run nf-core/rnaseq --input ./data/samplesheet.csv

## Next steps

- [Submitting Data](submitting-data.md) — Full walkthrough of the submission process
- [CLI Reference](cli.md) — Full CLI command reference
- [API Overview](../api/overview.md) — Programmatic access for bioinformaticians
- [Bulk Submission](bulk-submission.md) — Submit many samples at once
