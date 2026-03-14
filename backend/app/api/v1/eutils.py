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
    rettype: str = Query("json", pattern="^(json|xml)$"),
):
    """List available databases and their searchable fields."""
    databases = []
    for db_name in DB_CONFIG:
        fields = []
        for field_code, field_dbs in FIELD_MAP.items():
            if db_name in field_dbs:
                fields.append(field_code)
        databases.append({
            "name": db_name,
            "description": f"SeqDB {db_name} records",
            "fields": fields,
            "count": None,
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
    rettype: str = Query("json", pattern="^(json|xml)$"),
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
    rettype: str = Query("json", pattern="^(json|xml)$"),
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
    rettype: str = Query("json", pattern="^(json|xml)$"),
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
