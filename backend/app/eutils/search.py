"""Map parsed Entrez queries to SQLAlchemy filters."""

from datetime import date
from sqlalchemy import or_, and_, not_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.sample import Sample
from app.models.experiment import Experiment
from app.eutils.parser import QueryTerm


# Maps NCBI field qualifiers to SQLAlchemy model column names per database.
FIELD_MAP = {
    "ORGN": {
        "biosample": "organism",
    },
    "TITL": {
        "bioproject": "title",
        "biosample": "organism",
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
    """Convert parsed query tokens into a SQLAlchemy filter clause."""
    config = DB_CONFIG.get(db)
    if not config:
        return None

    model = config["model"]
    clauses = []
    pending_op = "AND"

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
    """Execute a search and return accession list."""
    config = DB_CONFIG.get(db)
    if not config:
        return {"count": 0, "ids": [], "retstart": retstart, "retmax": retmax}

    model = config["model"]
    filter_clause = build_query_filter(tokens, db)

    # Count query
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
    """Fetch full records by accession list."""
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
