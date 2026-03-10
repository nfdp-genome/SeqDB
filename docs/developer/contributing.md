# Contributing

## Project structure

```
SeqDB/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/v1/    # Route handlers
│   │   ├── models/    # SQLAlchemy ORM models
│   │   ├── schemas/   # Pydantic request/response schemas
│   │   └── services/  # Business logic
│   └── tests/
├── cli/               # seqdb-cli (Python CLI tool)
│   ├── src/seqdb_cli/ # CLI source code
│   └── tests/
├── frontend/          # Next.js frontend
│   └── src/
│       ├── app/       # Pages (App Router)
│       ├── components/# React components
│       └── lib/       # API client, utilities
├── docs/              # Documentation (MkDocs)
└── mkdocs.yml         # Docs config
```

## Code conventions

### Backend (Python)

- **Async everywhere** — All database operations use `async/await`
- **Service layer** — Business logic in `services/`, not in route handlers
- **Pydantic schemas** — Request/response validation via Pydantic v2
- **Accession generation** — Use `generate_accession()` from `services/accession.py`

### Frontend (TypeScript)

- **App Router** — Next.js App Router with `"use client"` for interactive pages
- **React Query** — All API calls via `useQuery` / `useMutation`
- **shadcn/ui** — UI components from shadcn/ui library
- **Tailwind CSS** — Styling via utility classes

## Adding a new API endpoint

1. Create or edit the route handler in `backend/app/api/v1/`
2. Add Pydantic schemas in `backend/app/schemas/`
3. Add business logic in `backend/app/services/`
4. Register the router in `backend/app/api/v1/router.py`
5. Add tests in `backend/tests/`

## Adding documentation

1. Create a new `.md` file in the appropriate `docs/` subdirectory
2. Add the page to the `nav` section in `mkdocs.yml`
3. Preview locally with `mkdocs serve`

## Branching

- `main` — Production-ready code
- `feature/*` — Feature branches
- `fix/*` — Bug fixes

## Commit messages

Use conventional commits:

```
feat: add file report endpoint
fix: handle empty collection_date in bulk submit
docs: add API guide for file reports
```
