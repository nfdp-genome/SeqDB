import pytest
import pytest_asyncio

from app.services.runs import create_run


@pytest_asyncio.fixture
async def seeded_project(client, db, auth_headers):
    """Create a project with samples, experiments, and runs for samplesheet testing."""
    r = await client.post("/api/v1/projects", json={
        "title": "Camel Genotyping Study",
        "description": "iScan genotyping of dromedary camels",
        "project_type": "Genotyping",
    }, headers=auth_headers)
    assert r.status_code == 201
    proj_acc = r.json()["accession"]

    r = await client.post("/api/v1/samples", json={
        "project_accession": proj_acc,
        "checklist_id": "ERC000011",
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "collection_date": "2026-01-15",
        "geographic_location": "Saudi Arabia:Riyadh",
        "breed": "Majaheem",
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

    # Create two runs (paired FASTQ files)
    run1 = await create_run(
        db, experiment_accession=exp_acc,
        file_type="FASTQ", file_path="sample1_R1.fastq.gz",
        file_size=1024000, checksum_md5="abc123def456",
    )
    run2 = await create_run(
        db, experiment_accession=exp_acc,
        file_type="FASTQ", file_path="sample1_R2.fastq.gz",
        file_size=1024000, checksum_md5="def456abc123",
    )
    await db.commit()

    return {
        "project": proj_acc, "sample": sample_acc, "experiment": exp_acc,
        "runs": [run1.internal_accession, run2.internal_accession],
    }


@pytest.mark.asyncio
async def test_samplesheet_generic(client, auth_headers, seeded_project):
    r = await client.get(
        f"/api/v1/samplesheet/{seeded_project['project']}",
        params={"format": "generic"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    text = r.text
    assert "project_accession" in text
    assert "sample_accession" in text
    assert "download_url" in text
    assert seeded_project["project"] in text


@pytest.mark.asyncio
async def test_samplesheet_fetchngs(client, auth_headers, seeded_project):
    r = await client.get(
        f"/api/v1/samplesheet/{seeded_project['project']}",
        params={"format": "fetchngs"},
    )
    assert r.status_code == 200
    text = r.text
    lines = [l.strip() for l in text.strip().splitlines()]
    assert lines[0] == "sample,fastq_1,fastq_2"
    assert seeded_project["sample"] in lines[1]


@pytest.mark.asyncio
async def test_samplesheet_sarek(client, auth_headers, seeded_project):
    r = await client.get(
        f"/api/v1/samplesheet/{seeded_project['project']}",
        params={"format": "sarek"},
    )
    assert r.status_code == 200
    text = r.text
    assert "patient,sample,lane,fastq_1,fastq_2" in text
    assert seeded_project["project"] in text


@pytest.mark.asyncio
async def test_samplesheet_rnaseq(client, auth_headers, seeded_project):
    r = await client.get(
        f"/api/v1/samplesheet/{seeded_project['project']}",
        params={"format": "rnaseq"},
    )
    assert r.status_code == 200
    text = r.text
    assert "sample,fastq_1,fastq_2,strandedness" in text


@pytest.mark.asyncio
async def test_samplesheet_snpchip(client, auth_headers, seeded_project):
    r = await client.get(
        f"/api/v1/samplesheet/{seeded_project['project']}",
        params={"format": "snpchip"},
    )
    assert r.status_code == 200
    text = r.text
    assert "sample" in text
    assert "organism" in text
    assert "Camelus dromedarius" in text


@pytest.mark.asyncio
async def test_samplesheet_not_found(client):
    r = await client.get("/api/v1/samplesheet/NFDP-PRJ-999999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_samplesheet_content_disposition(client, auth_headers, seeded_project):
    r = await client.get(
        f"/api/v1/samplesheet/{seeded_project['project']}",
        params={"format": "fetchngs"},
    )
    assert r.status_code == 200
    cd = r.headers.get("content-disposition", "")
    assert "fetchngs_samplesheet.csv" in cd
