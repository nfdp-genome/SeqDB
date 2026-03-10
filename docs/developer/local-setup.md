# Local Development Setup

## Prerequisites

- Python 3.12+
- Node.js 20+ and npm
- Git

Optional (for full stack):

- Docker and Docker Compose (for PostgreSQL, MinIO, Redis)

## Quick start (SQLite mode)

The simplest setup uses SQLite — no Docker required.

### Backend

```bash
cd SeqDB/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"

# Set up environment
cp ../.env.example ../.env
# The default .env uses SQLite: DATABASE_URL=sqlite+aiosqlite:///dev.db

# Start the server
uvicorn app.main:app --reload --port 8000
```

The backend creates all database tables automatically on startup.

### Frontend

```bash
cd SeqDB/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Open `http://localhost:3000` in your browser.

## Full stack (Docker Compose)

For production-like setup with PostgreSQL, MinIO, and Redis:

```bash
cd SeqDB

# Start all services
docker-compose up -d

# Backend connects to PostgreSQL, MinIO, Redis automatically
cd backend
uvicorn app.main:app --reload --port 8000
```

### docker-compose.yml services

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Metadata database |
| MinIO | 9000 (API), 9001 (console) | Object storage |
| Redis | 6379 | Job queue |

## Environment variables

| Variable | Default (dev) | Description |
|----------|--------------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///dev.db` | Database connection |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO server |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO access key |
| `MINIO_SECRET_KEY` | `minioadmin` | MinIO secret key |
| `MINIO_SECURE` | `false` | Use TLS for MinIO |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `JWT_SECRET_KEY` | `test-secret-key` | JWT signing key |
| `APP_ENV` | `development` | Environment name |

## Running tests

```bash
cd backend
pytest tests/ -v
```

## Building docs locally

```bash
pip install mkdocs-material mkdocstrings[python] pymdown-extensions

# Serve docs with live reload
mkdocs serve

# Build static site
mkdocs build
```

Docs available at `http://localhost:8000` (default mkdocs port).

## Database management

### SQLite (dev)

The `dev.db` file is created automatically. To reset:

```bash
rm dev.db
# Restart the backend — tables are recreated
```

### PostgreSQL (production)

```bash
# Run migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "description"
```
