import pytest
from datetime import date, datetime
from pydantic import ValidationError
from app.schemas.project import ProjectCreate, ProjectResponse
from app.schemas.sample import SampleCreate, SampleResponse
from app.schemas.experiment import ExperimentCreate, ExperimentResponse
from app.schemas.run import RunResponse


def test_project_create_valid():
    s = ProjectCreate(
        title="Camel WGS",
        description="WGS of dromedary camels",
        project_type="WGS",
    )
    assert s.title == "Camel WGS"


def test_project_create_missing_required():
    with pytest.raises(ValidationError):
        ProjectCreate(title="No description")


def test_sample_create_valid():
    s = SampleCreate(
        project_accession="NFDP-PRJ-000001",
        checklist_id="ERC000055",
        organism="Camelus dromedarius",
        tax_id=9838,
        collection_date=date(2026, 1, 15),
        geographic_location="Saudi Arabia:Riyadh",
    )
    assert s.tax_id == 9838


def test_sample_create_invalid_accession():
    with pytest.raises(ValidationError):
        SampleCreate(
            project_accession="INVALID",
            checklist_id="ERC000055",
            organism="Camelus dromedarius",
            tax_id=9838,
            collection_date=date(2026, 1, 15),
            geographic_location="Saudi Arabia:Riyadh",
        )


def test_experiment_create_valid():
    e = ExperimentCreate(
        sample_accession="NFDP-SAM-000001",
        platform="ILLUMINA",
        instrument_model="NovaSeq 6000",
        library_strategy="WGS",
        library_source="GENOMIC",
        library_layout="PAIRED",
        insert_size=350,
    )
    assert e.platform.value == "ILLUMINA"


def test_experiment_create_invalid_accession():
    with pytest.raises(ValidationError):
        ExperimentCreate(
            sample_accession="BAD",
            platform="ILLUMINA",
            instrument_model="NovaSeq 6000",
            library_strategy="WGS",
            library_source="GENOMIC",
            library_layout="PAIRED",
        )


# --- Chunk 1: NCBI Data Model Alignment schema tests ---


def test_project_response_has_ncbi_accession():
    resp = ProjectResponse(
        accession="NFDP-PRJ-000001",
        ena_accession=None,
        title="Test",
        description="desc",
        project_type="WGS",
        license="CC-BY",
        created_at=datetime(2026, 1, 1),
    )
    assert resp.ncbi_accession is None
    resp2 = ProjectResponse(
        accession="NFDP-PRJ-000002",
        ncbi_accession="PRJNA123456",
        title="Test2",
        description="desc2",
        project_type="WGS",
        license="CC-BY",
        created_at=datetime(2026, 1, 1),
    )
    assert resp2.ncbi_accession == "PRJNA123456"


def test_sample_response_has_ncbi_accession_and_domain_schema_id():
    resp = SampleResponse(
        accession="NFDP-SAM-000001",
        ena_accession=None,
        organism="Camelus dromedarius",
        tax_id=9838,
        checklist_id="ERC000055",
        created_at=datetime(2026, 1, 1),
    )
    assert resp.ncbi_accession is None
    assert resp.domain_schema_id is None

    resp2 = SampleResponse(
        accession="NFDP-SAM-000002",
        ncbi_accession="SAMN12345678",
        domain_schema_id="livestock.1.0",
        organism="Camelus dromedarius",
        tax_id=9838,
        checklist_id="ERC000055",
        created_at=datetime(2026, 1, 1),
    )
    assert resp2.ncbi_accession == "SAMN12345678"
    assert resp2.domain_schema_id == "livestock.1.0"


def test_sample_create_accepts_domain_schema_id():
    s = SampleCreate(
        project_accession="NFDP-PRJ-000001",
        checklist_id="ERC000055",
        organism="Camelus dromedarius",
        tax_id=9838,
        domain_schema_id="livestock.1.0",
    )
    assert s.domain_schema_id == "livestock.1.0"

    s2 = SampleCreate(
        project_accession="NFDP-PRJ-000001",
        checklist_id="ERC000055",
        organism="Camelus dromedarius",
        tax_id=9838,
    )
    assert s2.domain_schema_id is None


def test_experiment_response_has_ncbi_accession():
    from app.models.enums import Platform, LibraryStrategy, LibrarySource, LibraryLayout
    resp = ExperimentResponse(
        accession="NFDP-EXP-000001",
        platform=Platform.ILLUMINA,
        instrument_model="NovaSeq 6000",
        library_strategy=LibraryStrategy.WGS,
        library_source=LibrarySource.GENOMIC,
        library_layout=LibraryLayout.PAIRED,
        created_at=datetime(2026, 1, 1),
    )
    assert resp.ncbi_accession is None

    resp2 = ExperimentResponse(
        accession="NFDP-EXP-000002",
        ncbi_accession="SRX123456",
        platform=Platform.ILLUMINA,
        instrument_model="NovaSeq 6000",
        library_strategy=LibraryStrategy.WGS,
        library_source=LibrarySource.GENOMIC,
        library_layout=LibraryLayout.PAIRED,
        created_at=datetime(2026, 1, 1),
    )
    assert resp2.ncbi_accession == "SRX123456"


def test_run_response_has_ncbi_accession():
    from app.models.enums import FileType
    resp = RunResponse(
        accession="NFDP-RUN-000001",
        file_type=FileType.FASTQ,
        file_size=1000000,
        checksum_md5="d41d8cd98f00b204e9800998ecf8427e",
        created_at=datetime(2026, 1, 1),
    )
    assert resp.ncbi_accession is None

    resp2 = RunResponse(
        accession="NFDP-RUN-000002",
        ncbi_accession="SRR123456",
        file_type=FileType.FASTQ,
        file_size=1000000,
        checksum_md5="d41d8cd98f00b204e9800998ecf8427e",
        created_at=datetime(2026, 1, 1),
    )
    assert resp2.ncbi_accession == "SRR123456"
