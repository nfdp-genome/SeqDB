from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from rapidfuzz import fuzz

from app.models.enums import OntologyType
from app.models.ontology_term import OntologyTerm


class OntologyResolver:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_term(self, value: str, ontology: OntologyType) -> dict:
        # Exact label match
        result = await self.db.execute(
            select(OntologyTerm).where(
                OntologyTerm.ontology == ontology,
                OntologyTerm.label == value,
                OntologyTerm.is_obsolete == False,
            )
        )
        term = result.scalar_one_or_none()
        if term:
            return {"valid": True, "term_id": term.term_id}

        # Synonym match
        result = await self.db.execute(
            select(OntologyTerm).where(
                OntologyTerm.ontology == ontology,
                OntologyTerm.is_obsolete == False,
            )
        )
        all_terms = result.scalars().all()

        for term in all_terms:
            if term.synonyms and value.lower() in [s.lower() for s in term.synonyms]:
                return {"valid": True, "term_id": term.term_id}

        # Fuzzy match
        best_score = 0
        best_term = None
        for term in all_terms:
            score = fuzz.ratio(value.lower(), term.label.lower())
            if score > best_score:
                best_score = score
                best_term = term
            if term.synonyms:
                for syn in term.synonyms:
                    syn_score = fuzz.ratio(value.lower(), syn.lower())
                    if syn_score > best_score:
                        best_score = syn_score
                        best_term = term

        if best_score >= 80 and best_term:
            return {
                "valid": False,
                "suggestion": best_term.label,
                "term_id": best_term.term_id,
                "score": best_score,
            }

        return {"valid": False}

    async def search_terms(self, query: str, ontology: OntologyType, limit: int = 10) -> list[dict]:
        result = await self.db.execute(
            select(OntologyTerm).where(
                OntologyTerm.ontology == ontology,
                OntologyTerm.is_obsolete == False,
            )
        )
        all_terms = result.scalars().all()

        scored = []
        query_lower = query.lower()
        for term in all_terms:
            if term.label.lower().startswith(query_lower):
                scored.append((100, term))
            elif query_lower in term.label.lower():
                scored.append((90, term))
            else:
                matched = False
                if term.synonyms:
                    for syn in term.synonyms:
                        if query_lower in syn.lower():
                            scored.append((85, term))
                            matched = True
                            break
                if not matched:
                    score = fuzz.ratio(query_lower, term.label.lower())
                    if score >= 60:
                        scored.append((score, term))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"term_id": term.term_id, "label": term.label, "synonyms": term.synonyms or [], "ontology": term.ontology.value}
            for _, term in scored[:limit]
        ]

    async def lookup_term(self, term_id: str) -> dict | None:
        result = await self.db.execute(
            select(OntologyTerm).where(OntologyTerm.term_id == term_id)
        )
        term = result.scalar_one_or_none()
        if term is None:
            return None
        return {
            "term_id": term.term_id, "label": term.label, "synonyms": term.synonyms or [],
            "ontology": term.ontology.value, "parent_id": term.parent_id, "is_obsolete": term.is_obsolete,
        }
