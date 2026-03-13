import pytest
from app.ontologies.loader import seed_ontology_terms
from app.models.enums import OntologyType


@pytest.mark.asyncio
async def test_ontology_search(client, db):
    await seed_ontology_terms(db, "ncbi_taxonomy_livestock", OntologyType.NCBI_TAXONOMY)
    response = await client.get(
        "/api/v1/ontologies/search",
        params={"q": "camel", "ontology": "ncbi_taxonomy", "limit": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    labels = [t["label"] for t in data]
    assert "Camelus dromedarius" in labels


@pytest.mark.asyncio
async def test_ontology_search_missing_params(client):
    response = await client.get("/api/v1/ontologies/search")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ontology_search_empty_results(client, db):
    await seed_ontology_terms(db, "ncbi_taxonomy_livestock", OntologyType.NCBI_TAXONOMY)
    response = await client.get(
        "/api/v1/ontologies/search",
        params={"q": "xyznonexistent", "ontology": "ncbi_taxonomy"},
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_ontology_seed_endpoint(client, auth_headers, db):
    response = await client.post("/api/v1/ontologies/seed", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "ncbi_taxonomy" in data
    assert data["ncbi_taxonomy"] > 0
