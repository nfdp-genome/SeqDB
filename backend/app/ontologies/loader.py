import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import OntologyType
from app.models.ontology_term import OntologyTerm

_SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"


def load_snapshot(snapshot_name: str) -> list[dict]:
    path = _SNAPSHOTS_DIR / f"{snapshot_name}.json"
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    return data.get("terms", [])


async def seed_ontology_terms(
    db: AsyncSession, snapshot_name: str, ontology_type: OntologyType,
) -> int:
    terms = load_snapshot(snapshot_name)
    if not terms:
        return 0

    for term_data in terms:
        result = await db.execute(
            select(OntologyTerm).where(
                OntologyTerm.ontology == ontology_type,
                OntologyTerm.term_id == term_data["term_id"],
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.label = term_data["label"]
            existing.synonyms = term_data.get("synonyms", [])
            existing.parent_id = term_data.get("parent_id")
            existing.last_updated = datetime.utcnow()
        else:
            db.add(OntologyTerm(
                ontology=ontology_type,
                term_id=term_data["term_id"],
                label=term_data["label"],
                synonyms=term_data.get("synonyms", []),
                parent_id=term_data.get("parent_id"),
                is_obsolete=False,
            ))

    await db.commit()
    return len(terms)
