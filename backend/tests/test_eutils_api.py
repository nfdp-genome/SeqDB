import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def seed_data(client, auth_headers):
    """Seed a project, sample, and experiment for eutils testing."""
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
async def test_efetch_biosample(client, auth_headers, seed_data):
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
