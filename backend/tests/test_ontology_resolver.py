import pytest
from app.ontologies.loader import load_snapshot, seed_ontology_terms
from app.ontologies.resolver import OntologyResolver
from app.services.ontology_service import OntologyService
from app.models.ontology_term import OntologyTerm
from app.models.enums import OntologyType
from sqlalchemy import select


def test_load_snapshot_ncbi_taxonomy():
    terms = load_snapshot("ncbi_taxonomy_livestock")
    assert len(terms) > 0
    assert terms[0]["term_id"].startswith("NCBITaxon:")


def test_load_snapshot_not_found():
    terms = load_snapshot("nonexistent")
    assert terms == []


@pytest.mark.asyncio
async def test_seed_ontology_terms(db):
    count = await seed_ontology_terms(db, "ncbi_taxonomy_livestock", OntologyType.NCBI_TAXONOMY)
    assert count > 0
    result = await db.execute(
        select(OntologyTerm).where(OntologyTerm.term_id == "NCBITaxon:9838")
    )
    term = result.scalar_one_or_none()
    assert term is not None
    assert term.label == "Camelus dromedarius"
    assert "dromedary" in term.synonyms


@pytest.mark.asyncio
async def test_seed_is_idempotent(db):
    count1 = await seed_ontology_terms(db, "ncbi_taxonomy_livestock", OntologyType.NCBI_TAXONOMY)
    count2 = await seed_ontology_terms(db, "ncbi_taxonomy_livestock", OntologyType.NCBI_TAXONOMY)
    assert count1 == count2


@pytest.mark.asyncio
async def test_validate_term_exact_match(db):
    await seed_ontology_terms(db, "ncbi_taxonomy_livestock", OntologyType.NCBI_TAXONOMY)
    resolver = OntologyResolver(db)
    result = await resolver.validate_term("Camelus dromedarius", OntologyType.NCBI_TAXONOMY)
    assert result["valid"] is True
    assert result["term_id"] == "NCBITaxon:9838"


@pytest.mark.asyncio
async def test_validate_term_synonym_match(db):
    await seed_ontology_terms(db, "ncbi_taxonomy_livestock", OntologyType.NCBI_TAXONOMY)
    resolver = OntologyResolver(db)
    result = await resolver.validate_term("dromedary", OntologyType.NCBI_TAXONOMY)
    assert result["valid"] is True
    assert result["term_id"] == "NCBITaxon:9838"


@pytest.mark.asyncio
async def test_validate_term_fuzzy_match(db):
    await seed_ontology_terms(db, "ncbi_taxonomy_livestock", OntologyType.NCBI_TAXONOMY)
    resolver = OntologyResolver(db)
    result = await resolver.validate_term("Camelus dromadarius", OntologyType.NCBI_TAXONOMY)
    assert result["valid"] is False
    assert result.get("suggestion") is not None


@pytest.mark.asyncio
async def test_validate_term_no_match(db):
    await seed_ontology_terms(db, "ncbi_taxonomy_livestock", OntologyType.NCBI_TAXONOMY)
    resolver = OntologyResolver(db)
    result = await resolver.validate_term("Unicornus magicus", OntologyType.NCBI_TAXONOMY)
    assert result["valid"] is False


@pytest.mark.asyncio
async def test_search_terms(db):
    await seed_ontology_terms(db, "ncbi_taxonomy_livestock", OntologyType.NCBI_TAXONOMY)
    resolver = OntologyResolver(db)
    results = await resolver.search_terms("camel", OntologyType.NCBI_TAXONOMY, limit=5)
    assert len(results) >= 1
    labels = [r["label"] for r in results]
    assert "Camelus dromedarius" in labels


@pytest.mark.asyncio
async def test_lookup_term(db):
    await seed_ontology_terms(db, "ncbi_taxonomy_livestock", OntologyType.NCBI_TAXONOMY)
    resolver = OntologyResolver(db)
    result = await resolver.lookup_term("NCBITaxon:9838")
    assert result is not None
    assert result["label"] == "Camelus dromedarius"


@pytest.mark.asyncio
async def test_lookup_term_not_found(db):
    await seed_ontology_terms(db, "ncbi_taxonomy_livestock", OntologyType.NCBI_TAXONOMY)
    resolver = OntologyResolver(db)
    result = await resolver.lookup_term("NCBITaxon:9999999")
    assert result is None


@pytest.mark.asyncio
async def test_seed_all_ontologies(db):
    service = OntologyService(db)
    counts = await service.seed_all()
    assert "ncbi_taxonomy" in counts
    assert "lbo" in counts
    assert "gaz" in counts
    assert "efo" in counts
    assert "envo" in counts
    assert all(c > 0 for c in counts.values())
