import pytest
from datetime import date
from pydantic import ValidationError
from app.schemas.project import ProjectCreate, ProjectResponse
from app.schemas.sample import SampleCreate
from app.schemas.experiment import ExperimentCreate


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
