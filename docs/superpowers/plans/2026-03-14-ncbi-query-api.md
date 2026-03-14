# NCBI-style Query API Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add E-utilities-style query endpoints (einfo, esearch, efetch, esummary) so external tools can query SeqDB using familiar NCBI patterns.

**Architecture:** A query parser translates Entrez-style syntax (`organism[ORGN] AND camel[TITL]`) into SQLAlchemy filters. A search engine maps parsed queries to the correct model. Serializers format responses as JSON (default) or NCBI-compatible XML. All endpoints live under `/api/v1/eutils/`.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 async, xml.etree.ElementTree, pytest + pytest-asyncio

**Spec:** `docs/superpowers/specs/2026-03-14-ncbi-query-api-design.md`

---

## File Structure

### New files to create

| File | Responsibility |
|------|---------------|
| `backend/app/eutils/__init__.py` | Package init |
| `backend/app/eutils/parser.py` | Parse Entrez query syntax into structured tokens |
| `backend/app/eutils/search.py` | Map parsed queries to SQLAlchemy filters and execute |
| `backend/app/eutils/serializers.py` | JSON and XML response formatting |
| `backend/app/api/v1/eutils.py` | E-utilities API endpoints |
| `backend/tests/test_eutils_parser.py` | Query parser tests |
| `backend/tests/test_eutils_api.py` | Endpoint integration tests |

### Existing files to modify

| File | Change |
|------|--------|
| `backend/app/api/v1/router.py` | Register eutils router |

---

## Chunk 1: Query Parser

### Task 1: Create Entrez query parser

The parser translates NCBI Entrez-style query strings into structured token lists that the search engine can process. It supports field-qualified terms (`organism[ORGN]`), boolean operators (`AND`, `OR`, `NOT`), date ranges (`2026/01/01:2026/12/31[PDAT]`), and plain text search.

**Files:**
- Create: `backend/app/eutils/__init__.py`
- Create: `backend/app/eutils/parser.py`
- Create: `backend/tests/test_eutils_parser.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_eutils_parser.py`:

```python
import pytest
from app.eutils.parser import parse_query, QueryTerm


def test_simple_text():
    tokens = parse_query("camel WGS")
    assert len(tokens) == 1
    assert tokens[0].text == "camel WGS"
    assert tokens[0].field is None
    assert tokens[0].operator is None


def test_field_qualified_single():
    tokens = parse_query("Camelus dromedarius[ORGN]")
    assert len(tokens) == 1
    assert tokens[0].text == "Camelus dromedarius"
    assert tokens[0].field == "ORGN"


def test_boolean_and():
    tokens = parse_query("Camelus[ORGN] AND WGS[TITL]")
    assert len(tokens) == 3
    assert tokens[0].text == "Camelus"
    assert tokens[0].field == "ORGN"
    assert tokens[1].operator == "AND"
    assert tokens[2].text == "WGS"
    assert tokens[2].field == "TITL"


def test_boolean_or():
    tokens = parse_query("camel[ORGN] OR horse[ORGN]")
    assert len(tokens) == 3
    assert tokens[1].operator == "OR"


def test_boolean_not():
    tokens = parse_query("Camelus[ORGN] NOT dromedarius[TITL]")
    assert len(tokens) == 3
    assert tokens[1].operator == "NOT"


def test_accession_lookup():
    tokens = parse_query("NFDP-PRJ-000001")
    assert len(tokens) == 1
    assert tokens[0].text == "NFDP-PRJ-000001"
    assert tokens[0].field is None


def test_date_range():
    tokens = parse_query("2026/01/01:2026/12/31[PDAT]")
    assert len(tokens) == 1
    assert tokens[0].field == "PDAT"
    assert tokens[0].date_from == "2026/01/01"
    assert tokens[0].date_to == "2026/12/31"


def test_complex_query():
    tokens = parse_query("Camelus[ORGN] AND 2026/01/01:2026/06/30[PDAT]")
    assert len(tokens) == 3
    assert tokens[0].field == "ORGN"
    assert tokens[1].operator == "AND"
    assert tokens[2].field == "PDAT"
    assert tokens[2].date_from == "2026/01/01"


def test_empty_query():
    tokens = parse_query("")
    assert tokens == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/alarawms/dev/nfldp/SeqDB/backend && python -m pytest tests/test_eutils_parser.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

Create `backend/app/eutils/__init__.py` (empty file).

Create `backend/app/eutils/parser.py`:

```python
"""Parse NCBI Entrez-style query strings into structured tokens."""

import re
from dataclasses import dataclass, field


@dataclass
class QueryTerm:
    """A single parsed query term."""
    text: str = ""
    field: str | None = None
    operator: str | None = None
    date_from: str | None = None
    date_to: str | None = None


# Pattern for date range: YYYY/MM/DD:YYYY/MM/DD[FIELD]
_DATE_RANGE_RE = re.compile(
    r"(\d{4}/\d{2}/\d{2}):(\d{4}/\d{2}/\d{2})\[([A-Z]+)\]"
)

# Pattern for field-qualified term: text[FIELD]
_FIELD_QUAL_RE = re.compile(r"(.+?)\[([A-Z]+)\]")

# Boolean operators
_BOOLEAN_OPS = {"AND", "OR", "NOT"}


def parse_query(query: str) -> list[QueryTerm]:
    """Parse an Entrez-style query string into a list of QueryTerms.

    Supports:
    - Field-qualified: organism[ORGN], camel[TITL]
    - Boolean: AND, OR, NOT
    - Date range: 2026/01/01:2026/12/31[PDAT]
    - Plain text: camel WGS
    - Accession: NFDP-PRJ-000001
    """
    query = query.strip()
    if not query:
        return []

    tokens = []
    remaining = query

    while remaining:
        remaining = remaining.strip()
        if not remaining:
            break

        # Try date range first
        date_match = _DATE_RANGE_RE.match(remaining)
        if date_match:
            tokens.append(QueryTerm(
                text=date_match.group(0),
                field=date_match.group(3),
                date_from=date_match.group(1),
                date_to=date_match.group(2),
            ))
            remaining = remaining[date_match.end():]
            continue

        # Check for boolean operator at start
        for op in _BOOLEAN_OPS:
            if remaining.startswith(op + " "):
                tokens.append(QueryTerm(operator=op))
                remaining = remaining[len(op):]
                break
        else:
            # Try field-qualified term
            # Find the next boolean operator to know where this term ends
            next_op_pos = len(remaining)
            for op in _BOOLEAN_OPS:
                pos = remaining.find(f" {op} ")
                if pos != -1 and pos < next_op_pos:
                    next_op_pos = pos

            chunk = remaining[:next_op_pos].strip()
            remaining = remaining[next_op_pos:]

            if chunk:
                field_match = _FIELD_QUAL_RE.match(chunk)
                if field_match:
                    tokens.append(QueryTerm(
                        text=field_match.group(1).strip(),
                        field=field_match.group(2),
                    ))
                else:
                    tokens.append(QueryTerm(text=chunk))

    return tokens
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/alarawms/dev/nfldp/SeqDB/backend && python -m pytest tests/test_eutils_parser.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
cd /home/alarawms/dev/nfldp/SeqDB
git add backend/app/eutils/ backend/tests/test_eutils_parser.py
git commit -m "feat: add Entrez-style query parser for E-utilities API"
```

---

## Chunk 2: Search Engine & Serializers

### Task 2: Create search engine

The search engine maps parsed query tokens to SQLAlchemy filters on the correct model (Project, Sample, Experiment). It resolves field qualifiers (ORGN→organism, TITL→title, PDAT→created_at) and applies boolean logic.

**Files:**
- Create: `backend/app/eutils/search.py`
- Modify: `backend/tests/test_eutils_parser.py` (add search engine tests)

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_eutils_parser.py`:

```python
from app.eutils.search import build_query_filter, FIELD_MAP, DB_CONFIG


def test_field_map_has_standard_fields():
    assert "ORGN" in FIELD_MAP
    assert "TITL" in FIELD_MAP
    assert "PDAT" in FIELD_MAP
    assert "ACCN" in FIELD_MAP


def test_db_config_bioproject():
    assert "bioproject" in DB_CONFIG
    cfg = DB_CONFIG["bioproject"]
    assert cfg["model"].__tablename__ == "projects"


def test_db_config_biosample():
    assert "biosample" in DB_CONFIG
    cfg = DB_CONFIG["biosample"]
    assert cfg["model"].__tablename__ == "samples"


def test_db_config_sra():
    assert "sra" in DB_CONFIG
    cfg = DB_CONFIG["sra"]
    assert cfg["model"].__tablename__ == "experiments"


def test_build_filter_simple_text():
    from app.eutils.parser import parse_query
    tokens = parse_query("camel")
    filter_clause = build_query_filter(tokens, "bioproject")
    # Should return a SQLAlchemy filter (not None)
    assert filter_clause is not None


def test_build_filter_field_qualified():
    from app.eutils.parser import parse_query
    tokens = parse_query("Camelus[ORGN]")
    filter_clause = build_query_filter(tokens, "biosample")
    assert filter_clause is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/alarawms/dev/nfldp/SeqDB/backend && python -m pytest tests/test_eutils_parser.py -v -k "field_map or db_config or build_filter"`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

Create `backend/app/eutils/search.py`:

```python
"""Map parsed Entrez queries to SQLAlchemy filters."""

from datetime import date
from sqlalchemy import or_, and_, not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.sample import Sample
from app.models.experiment import Experiment
from app.eutils.parser import QueryTerm


# Maps NCBI field qualifiers to SQLAlchemy model attributes.
# Each entry: field_code -> {db_name: (model, column_name)}
FIELD_MAP = {
    "ORGN": {
        "biosample": "organism",
    },
    "TITL": {
        "bioproject": "title",
        "biosample": "organism",  # samples don't have titles; search organism
    },
    "PDAT": {
        "bioproject": "created_at",
        "biosample": "created_at",
        "sra": "created_at",
    },
    "ACCN": {
        "bioproject": "internal_accession",
        "biosample": "internal_accession",
        "sra": "internal_accession",
    },
}

# Database configuration: maps db parameter to model and searchable columns.
DB_CONFIG = {
    "bioproject": {
        "model": Project,
        "text_columns": ["title", "description", "internal_accession",
                         "ena_accession", "ncbi_accession"],
    },
    "biosample": {
        "model": Sample,
        "text_columns": ["organism", "breed", "geographic_location",
                         "internal_accession", "ena_accession", "ncbi_accession"],
    },
    "sra": {
        "model": Experiment,
        "text_columns": ["instrument_model", "internal_accession",
                         "ena_accession", "ncbi_accession"],
    },
}


def build_query_filter(tokens: list[QueryTerm], db: str):
    """Convert parsed query tokens into a SQLAlchemy filter clause.

    Args:
        tokens: Parsed query terms from parse_query()
        db: Database name (bioproject, biosample, sra)

    Returns:
        SQLAlchemy filter clause, or None if no valid filters.
    """
    config = DB_CONFIG.get(db)
    if not config:
        return None

    model = config["model"]
    clauses = []
    pending_op = "AND"  # default combinator

    for token in tokens:
        if token.operator:
            pending_op = token.operator
            continue

        clause = _token_to_clause(token, model, db, config)
        if clause is None:
            continue

        if not clauses:
            clauses.append(clause)
        elif pending_op == "AND":
            clauses.append(clause)
        elif pending_op == "OR":
            if clauses:
                prev = clauses.pop()
                clauses.append(or_(prev, clause))
        elif pending_op == "NOT":
            clauses.append(not_(clause))

        pending_op = "AND"

    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return and_(*clauses)


def _token_to_clause(token: QueryTerm, model, db: str, config: dict):
    """Convert a single query term to a SQLAlchemy filter."""
    # Date range
    if token.date_from and token.date_to and token.field:
        col_name = FIELD_MAP.get(token.field, {}).get(db)
        if not col_name:
            col_name = "created_at"
        col = getattr(model, col_name, None)
        if col is None:
            return None
        try:
            parts_from = token.date_from.split("/")
            parts_to = token.date_to.split("/")
            d_from = date(int(parts_from[0]), int(parts_from[1]), int(parts_from[2]))
            d_to = date(int(parts_to[0]), int(parts_to[1]), int(parts_to[2]))
            return and_(col >= d_from, col <= d_to)
        except (ValueError, IndexError):
            return None

    # Field-qualified search
    if token.field:
        col_name = FIELD_MAP.get(token.field, {}).get(db)
        if not col_name:
            # Fall back to text search
            return _text_search(token.text, model, config)
        col = getattr(model, col_name, None)
        if col is None:
            return _text_search(token.text, model, config)
        return col.ilike(f"%{token.text}%")

    # Plain text / accession search
    return _text_search(token.text, model, config)


def _text_search(text: str, model, config: dict):
    """Full-text search across all searchable columns."""
    text_columns = config.get("text_columns", [])
    clauses = []
    for col_name in text_columns:
        col = getattr(model, col_name, None)
        if col is not None:
            clauses.append(col.ilike(f"%{text}%"))
    if not clauses:
        return None
    return or_(*clauses)


async def execute_search(
    db_session: AsyncSession,
    db: str,
    tokens: list[QueryTerm],
    retstart: int = 0,
    retmax: int = 20,
) -> dict:
    """Execute a search and return accession list.

    Returns:
        {"count": int, "ids": [str], "retstart": int, "retmax": int}
    """
    config = DB_CONFIG.get(db)
    if not config:
        return {"count": 0, "ids": [], "retstart": retstart, "retmax": retmax}

    model = config["model"]
    filter_clause = build_query_filter(tokens, db)

    # Count query
    from sqlalchemy import func
    count_q = select(func.count(model.id))
    if filter_clause is not None:
        count_q = count_q.where(filter_clause)
    count_result = await db_session.execute(count_q)
    total = count_result.scalar()

    # Result query
    query = select(model.internal_accession)
    if filter_clause is not None:
        query = query.where(filter_clause)
    query = query.order_by(model.created_at.desc()).offset(retstart).limit(retmax)
    result = await db_session.execute(query)
    ids = [row[0] for row in result.all()]

    return {"count": total, "ids": ids, "retstart": retstart, "retmax": retmax}


async def fetch_records(
    db_session: AsyncSession,
    db: str,
    ids: list[str],
) -> list[dict]:
    """Fetch full records by accession list.

    Returns list of dicts with all entity fields.
    """
    config = DB_CONFIG.get(db)
    if not config:
        return []

    model = config["model"]
    query = select(model).where(model.internal_accession.in_(ids))
    result = await db_session.execute(query)
    entities = result.scalars().all()

    records = []
    for entity in entities:
        record = {}
        for col in entity.__table__.columns:
            val = getattr(entity, col.name)
            if isinstance(val, date):
                val = val.isoformat()
            elif hasattr(val, "value"):
                val = val.value
            record[col.name] = val
        records.append(record)

    return records
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/alarawms/dev/nfldp/SeqDB/backend && python -m pytest tests/test_eutils_parser.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
cd /home/alarawms/dev/nfldp/SeqDB
git add backend/app/eutils/search.py backend/tests/test_eutils_parser.py
git commit -m "feat: add E-utilities search engine with field mapping and SQL filters"
```

---

### Task 3: Create response serializers

The serializers format search results and fetched records into JSON (default) or NCBI-compatible XML responses.

**Files:**
- Create: `backend/app/eutils/serializers.py`

- [ ] **Step 1: Write implementation**

Create `backend/app/eutils/serializers.py`:

```python
"""JSON and XML response serializers for E-utilities endpoints."""

from xml.etree.ElementTree import Element, SubElement, tostring
from datetime import date, datetime


def serialize_esearch_json(result: dict, db: str) -> dict:
    """Format esearch results as NCBI-style JSON."""
    return {
        "header": {"type": "esearch", "version": "0.3"},
        "esearchresult": {
            "db": db,
            "count": str(result["count"]),
            "retmax": str(result["retmax"]),
            "retstart": str(result["retstart"]),
            "idlist": result["ids"],
        },
    }


def serialize_esearch_xml(result: dict, db: str) -> str:
    """Format esearch results as NCBI-style XML."""
    root = Element("eSearchResult")
    SubElement(root, "Count").text = str(result["count"])
    SubElement(root, "RetMax").text = str(result["retmax"])
    SubElement(root, "RetStart").text = str(result["retstart"])
    id_list = SubElement(root, "IdList")
    for acc in result["ids"]:
        SubElement(id_list, "Id").text = acc
    return tostring(root, encoding="unicode", xml_declaration=True)


def serialize_efetch_json(records: list[dict], db: str) -> dict:
    """Format efetch results as JSON."""
    return {
        "header": {"type": "efetch", "version": "0.3"},
        "db": db,
        "count": len(records),
        "records": records,
    }


def serialize_efetch_xml(records: list[dict], db: str) -> str:
    """Format efetch results as NCBI-compatible XML."""
    root = Element("RecordSet", db=db)
    for record in records:
        rec_elem = SubElement(root, "Record")
        for key, value in record.items():
            if value is None:
                continue
            elem = SubElement(rec_elem, key)
            if isinstance(value, (date, datetime)):
                elem.text = value.isoformat()
            else:
                elem.text = str(value)
    return tostring(root, encoding="unicode", xml_declaration=True)


def serialize_esummary_json(records: list[dict], db: str) -> dict:
    """Format esummary results as JSON (lighter than efetch)."""
    summaries = []
    # Summary fields per db type
    summary_fields = {
        "bioproject": ["internal_accession", "title", "description",
                       "project_type", "created_at", "ncbi_accession"],
        "biosample": ["internal_accession", "organism", "tax_id", "breed",
                      "geographic_location", "created_at", "ncbi_accession"],
        "sra": ["internal_accession", "platform", "instrument_model",
                "library_strategy", "created_at", "ncbi_accession"],
    }
    fields = summary_fields.get(db, list(records[0].keys()) if records else [])

    for record in records:
        summary = {k: record.get(k) for k in fields if k in record}
        summaries.append(summary)

    return {
        "header": {"type": "esummary", "version": "0.3"},
        "db": db,
        "result": summaries,
    }


def serialize_esummary_xml(records: list[dict], db: str) -> str:
    """Format esummary results as XML."""
    root = Element("eSummaryResult")
    summary_fields = {
        "bioproject": ["internal_accession", "title", "project_type", "created_at"],
        "biosample": ["internal_accession", "organism", "tax_id", "breed", "created_at"],
        "sra": ["internal_accession", "platform", "instrument_model", "created_at"],
    }
    fields = summary_fields.get(db, [])

    for record in records:
        doc = SubElement(root, "DocumentSummary")
        for key in fields:
            val = record.get(key)
            if val is None:
                continue
            item = SubElement(doc, "Item", Name=key)
            item.text = str(val)

    return tostring(root, encoding="unicode", xml_declaration=True)


def serialize_einfo_json(databases: list[dict]) -> dict:
    """Format einfo results as JSON."""
    return {
        "header": {"type": "einfo", "version": "0.3"},
        "einforesult": {
            "dblist": [d["name"] for d in databases],
            "databases": databases,
        },
    }


def serialize_einfo_xml(databases: list[dict]) -> str:
    """Format einfo results as XML."""
    root = Element("eInfoResult")
    db_list = SubElement(root, "DbList")
    for db in databases:
        db_elem = SubElement(db_list, "DbName")
        db_elem.text = db["name"]
    return tostring(root, encoding="unicode", xml_declaration=True)
```

- [ ] **Step 2: Commit**

```bash
cd /home/alarawms/dev/nfldp/SeqDB
git add backend/app/eutils/serializers.py
git commit -m "feat: add JSON and XML serializers for E-utilities responses"
```

---

## Chunk 3: API Endpoints & Integration Tests

### Task 4: Create E-utilities API endpoints

The API endpoints expose the E-utilities interface: einfo (database listing), esearch (query), efetch (full records), esummary (summaries). Each supports `rettype=json|xml` for format selection.

**Files:**
- Create: `backend/app/api/v1/eutils.py`
- Modify: `backend/app/api/v1/router.py`

- [ ] **Step 1: Write implementation**

Create `backend/app/api/v1/eutils.py`:

```python
"""NCBI E-utilities-style query API endpoints."""

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.eutils.parser import parse_query
from app.eutils.search import (
    execute_search,
    fetch_records,
    DB_CONFIG,
    FIELD_MAP,
)
from app.eutils.serializers import (
    serialize_einfo_json,
    serialize_einfo_xml,
    serialize_esearch_json,
    serialize_esearch_xml,
    serialize_efetch_json,
    serialize_efetch_xml,
    serialize_esummary_json,
    serialize_esummary_xml,
)

router = APIRouter(prefix="/eutils", tags=["E-utilities"])


@router.get("/einfo")
async def einfo(
    rettype: str = Query("json", regex="^(json|xml)$"),
):
    """List available databases and their searchable fields."""
    databases = []
    for db_name, config in DB_CONFIG.items():
        fields = []
        for field_code, field_dbs in FIELD_MAP.items():
            if db_name in field_dbs:
                fields.append(field_code)
        databases.append({
            "name": db_name,
            "description": f"SeqDB {db_name} records",
            "fields": fields,
            "count": None,  # Would require DB query
        })

    if rettype == "xml":
        xml = serialize_einfo_xml(databases)
        return Response(content=xml, media_type="application/xml")
    return serialize_einfo_json(databases)


@router.get("/esearch")
async def esearch(
    db: str = Query(..., description="Database: bioproject, biosample, sra"),
    term: str = Query(..., min_length=1, description="Search query"),
    retstart: int = Query(0, ge=0),
    retmax: int = Query(20, ge=1, le=500),
    rettype: str = Query("json", regex="^(json|xml)$"),
    db_session: AsyncSession = Depends(get_db),
):
    """Search by query string, return accession list."""
    if db not in DB_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unknown database: {db}")

    tokens = parse_query(term)
    if not tokens:
        raise HTTPException(status_code=400, detail="Empty search query")

    result = await execute_search(db_session, db, tokens, retstart, retmax)

    if rettype == "xml":
        xml = serialize_esearch_xml(result, db)
        return Response(content=xml, media_type="application/xml")
    return serialize_esearch_json(result, db)


@router.get("/efetch")
async def efetch(
    db: str = Query(..., description="Database: bioproject, biosample, sra"),
    id: str = Query(..., description="Comma-separated accession list"),
    rettype: str = Query("json", regex="^(json|xml)$"),
    db_session: AsyncSession = Depends(get_db),
):
    """Fetch full records by accession."""
    if db not in DB_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unknown database: {db}")

    ids = [i.strip() for i in id.split(",") if i.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="No IDs provided")

    records = await fetch_records(db_session, db, ids)

    if rettype == "xml":
        xml = serialize_efetch_xml(records, db)
        return Response(content=xml, media_type="application/xml")
    return serialize_efetch_json(records, db)


@router.get("/esummary")
async def esummary(
    db: str = Query(..., description="Database: bioproject, biosample, sra"),
    id: str = Query(..., description="Comma-separated accession list"),
    rettype: str = Query("json", regex="^(json|xml)$"),
    db_session: AsyncSession = Depends(get_db),
):
    """Fetch summary records (lighter than efetch)."""
    if db not in DB_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unknown database: {db}")

    ids = [i.strip() for i in id.split(",") if i.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="No IDs provided")

    records = await fetch_records(db_session, db, ids)

    if rettype == "xml":
        xml = serialize_esummary_xml(records, db)
        return Response(content=xml, media_type="application/xml")
    return serialize_esummary_json(records, db)
```

Register in `backend/app/api/v1/router.py` — add after the ncbi_router import:
```python
from app.api.v1.eutils import router as eutils_router
```
And after the ncbi_router include:
```python
api_router.include_router(eutils_router)
```

- [ ] **Step 2: Commit**

```bash
cd /home/alarawms/dev/nfldp/SeqDB
git add backend/app/api/v1/eutils.py backend/app/api/v1/router.py
git commit -m "feat: add E-utilities API endpoints (einfo, esearch, efetch, esummary)"
```

---

### Task 5: Create integration tests

End-to-end tests that create test data, search for it, and fetch it through the E-utilities endpoints.

**Files:**
- Create: `backend/tests/test_eutils_api.py`

- [ ] **Step 1: Write the tests**

Create `backend/tests/test_eutils_api.py`:

```python
import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def seed_data(client, auth_headers):
    """Seed a project and sample for eutils testing."""
    r = await client.post("/api/v1/projects", json={
        "title": "Camel Genome Project",
        "description": "WGS of dromedary camels from Saudi Arabia",
        "project_type": "WGS",
    }, headers=auth_headers)
    assert r.status_code == 201
    project_acc = r.json()["accession"]

    r = await client.post("/api/v1/samples", json={
        "project_accession": project_acc,
        "checklist_id": "ERC000011",
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "collection_date": "2026-01-15",
        "geographic_location": "Saudi Arabia:Riyadh",
    }, headers=auth_headers)
    assert r.status_code == 201
    sample_acc = r.json()["accession"]

    r = await client.post("/api/v1/experiments", json={
        "sample_accession": sample_acc,
        "platform": "ILLUMINA",
        "instrument_model": "NovaSeq 6000",
        "library_strategy": "WGS",
        "library_source": "GENOMIC",
        "library_layout": "PAIRED",
    }, headers=auth_headers)
    assert r.status_code == 201
    exp_acc = r.json()["accession"]

    return {
        "project": project_acc,
        "sample": sample_acc,
        "experiment": exp_acc,
    }


# --- einfo ---

@pytest.mark.asyncio
async def test_einfo_json(client):
    r = await client.get("/api/v1/eutils/einfo")
    assert r.status_code == 200
    data = r.json()
    db_names = data["einforesult"]["dblist"]
    assert "bioproject" in db_names
    assert "biosample" in db_names
    assert "sra" in db_names


@pytest.mark.asyncio
async def test_einfo_xml(client):
    r = await client.get("/api/v1/eutils/einfo?rettype=xml")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/xml")
    assert "<DbName>bioproject</DbName>" in r.text


# --- esearch ---

@pytest.mark.asyncio
async def test_esearch_bioproject(client, auth_headers, seed_data):
    r = await client.get(
        "/api/v1/eutils/esearch",
        params={"db": "bioproject", "term": "Camel"},
    )
    assert r.status_code == 200
    data = r.json()
    assert int(data["esearchresult"]["count"]) >= 1
    assert seed_data["project"] in data["esearchresult"]["idlist"]


@pytest.mark.asyncio
async def test_esearch_biosample_organism(client, auth_headers, seed_data):
    r = await client.get(
        "/api/v1/eutils/esearch",
        params={"db": "biosample", "term": "Camelus dromedarius[ORGN]"},
    )
    assert r.status_code == 200
    data = r.json()
    assert int(data["esearchresult"]["count"]) >= 1


@pytest.mark.asyncio
async def test_esearch_invalid_db(client):
    r = await client.get(
        "/api/v1/eutils/esearch",
        params={"db": "invalid", "term": "test"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_esearch_xml(client, auth_headers, seed_data):
    r = await client.get(
        "/api/v1/eutils/esearch",
        params={"db": "bioproject", "term": "Camel", "rettype": "xml"},
    )
    assert r.status_code == 200
    assert "<Count>" in r.text


# --- efetch ---

@pytest.mark.asyncio
async def test_efetch_bioproject(client, auth_headers, seed_data):
    r = await client.get(
        "/api/v1/eutils/efetch",
        params={"db": "bioproject", "id": seed_data["project"]},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["records"]) == 1
    assert data["records"][0]["title"] == "Camel Genome Project"


@pytest.mark.asyncio
async def test_efetch_multiple(client, auth_headers, seed_data):
    r = await client.get(
        "/api/v1/eutils/efetch",
        params={"db": "biosample", "id": seed_data["sample"]},
    )
    assert r.status_code == 200
    assert len(r.json()["records"]) == 1


@pytest.mark.asyncio
async def test_efetch_xml(client, auth_headers, seed_data):
    r = await client.get(
        "/api/v1/eutils/efetch",
        params={"db": "bioproject", "id": seed_data["project"], "rettype": "xml"},
    )
    assert r.status_code == 200
    assert "<Record>" in r.text


# --- esummary ---

@pytest.mark.asyncio
async def test_esummary_bioproject(client, auth_headers, seed_data):
    r = await client.get(
        "/api/v1/eutils/esummary",
        params={"db": "bioproject", "id": seed_data["project"]},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["result"]) == 1
    assert "title" in data["result"][0]


@pytest.mark.asyncio
async def test_esummary_sra(client, auth_headers, seed_data):
    r = await client.get(
        "/api/v1/eutils/esummary",
        params={"db": "sra", "id": seed_data["experiment"]},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["result"]) == 1
    assert "platform" in data["result"][0]
```

- [ ] **Step 2: Run all tests**

Run: `cd /home/alarawms/dev/nfldp/SeqDB/backend && python -m pytest tests/test_eutils_parser.py tests/test_eutils_api.py -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
cd /home/alarawms/dev/nfldp/SeqDB
git add backend/tests/test_eutils_api.py
git commit -m "test: add E-utilities API integration tests"
```

---

### Task 6: Run full test suite and lint

**Files:**
- All modified files

- [ ] **Step 1: Run full test suite**

Run: `cd /home/alarawms/dev/nfldp/SeqDB/backend && python -m pytest tests/ -v --tb=short`
Expected: All tests pass

- [ ] **Step 2: Run linter on new files**

Run: `cd /home/alarawms/dev/nfldp/SeqDB && python -m ruff check backend/app/eutils/ backend/app/api/v1/eutils.py backend/tests/test_eutils_parser.py backend/tests/test_eutils_api.py`
Expected: Clean

- [ ] **Step 3: Fix any issues**

- [ ] **Step 4: Final commit if needed**

```bash
cd /home/alarawms/dev/nfldp/SeqDB
git add -A
git commit -m "fix: resolve lint and test issues from E-utilities API"
```
