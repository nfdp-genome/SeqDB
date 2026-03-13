from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import OntologyType
from app.ontologies.loader import seed_ontology_terms
from app.ontologies.resolver import OntologyResolver

_SNAPSHOT_MAP = {
    OntologyType.NCBI_TAXONOMY: "ncbi_taxonomy_livestock",
    OntologyType.GAZ: "gaz",
    OntologyType.EFO: "efo_sequencing",
    OntologyType.LBO: "lbo",
    OntologyType.ENVO: "envo",
}


class OntologyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.resolver = OntologyResolver(db)

    async def seed_all(self) -> dict[str, int]:
        counts = {}
        for ont_type, snapshot_name in _SNAPSHOT_MAP.items():
            count = await seed_ontology_terms(self.db, snapshot_name, ont_type)
            counts[ont_type.value] = count
        return counts

    async def validate_term(self, value: str, ontology: OntologyType) -> dict:
        return await self.resolver.validate_term(value, ontology)

    async def search_terms(self, query: str, ontology: OntologyType, limit: int = 10) -> list[dict]:
        return await self.resolver.search_terms(query, ontology, limit)

    async def lookup_term(self, term_id: str) -> dict | None:
        return await self.resolver.lookup_term(term_id)
