from app.plugins.exporters.ena_xml import (
    generate_study_xml,
    generate_sample_xml,
    generate_experiment_xml,
    generate_run_xml,
    generate_submission_xml,
)


def test_generate_study_xml():
    xml = generate_study_xml({
        "accession": "NFDP-PRJ-000001",
        "title": "Camel WGS",
        "description": "WGS of dromedary camels",
    })
    assert "<STUDY" in xml
    assert "Camel WGS" in xml
    assert 'alias="NFDP-PRJ-000001"' in xml


def test_generate_sample_xml():
    xml = generate_sample_xml({
        "accession": "NFDP-SAM-000001",
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "checklist_id": "ERC000055",
    })
    assert "<SAMPLE" in xml
    assert "9838" in xml
    assert "ERC000055" in xml
    assert "Camelus dromedarius" in xml


def test_generate_experiment_xml():
    xml = generate_experiment_xml({
        "accession": "NFDP-EXP-000001",
        "project_accession": "NFDP-PRJ-000001",
        "sample_accession": "NFDP-SAM-000001",
        "platform": "ILLUMINA",
        "instrument_model": "NovaSeq 6000",
        "library_strategy": "WGS",
        "library_source": "GENOMIC",
        "library_layout": "PAIRED",
    })
    assert "<EXPERIMENT" in xml
    assert "NovaSeq 6000" in xml


def test_generate_run_xml():
    xml = generate_run_xml({
        "accession": "NFDP-RUN-000001",
        "experiment_accession": "NFDP-EXP-000001",
        "filename": "sample_R1.fastq.gz",
        "file_type": "FASTQ",
        "checksum_md5": "abc123",
    })
    assert "<RUN" in xml
    assert "sample_R1.fastq.gz" in xml
    assert "abc123" in xml


def test_generate_submission_xml():
    xml = generate_submission_xml("NFDP-SUB-000001")
    assert "<SUBMISSION" in xml
    assert "ADD" in xml
