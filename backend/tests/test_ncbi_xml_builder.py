from xml.etree import ElementTree as ET

from app.ncbi.xml_builder import (
    build_submission_xml,
    build_bioproject_xml,
    build_biosample_xml,
    build_sra_xml,
)


def test_build_submission_xml():
    xml_str = build_submission_xml(
        action="AddData",
        target_db="BioProject",
        center_name="NFDP",
        submitter_email="admin@nfdp.dev",
    )
    root = ET.fromstring(xml_str)
    assert root.tag == "Submission"
    assert root.find(".//Action").attrib.get("name") == "AddData"


def test_build_bioproject_xml():
    project = {
        "title": "Camel WGS Study 2026",
        "description": "Whole genome sequencing of Arabian camels",
        "project_type": "WGS",
        "internal_accession": "NFDP-PRJ-000001",
    }
    xml_str = build_bioproject_xml(project, center_name="NFDP")
    root = ET.fromstring(xml_str)
    assert root.tag == "Project"
    title_elem = root.find(".//ProjectDescr/Title")
    assert title_elem is not None
    assert title_elem.text == "Camel WGS Study 2026"
    desc_elem = root.find(".//ProjectDescr/Description")
    assert desc_elem.text == "Whole genome sequencing of Arabian camels"


def test_build_bioproject_xml_has_spuid():
    project = {
        "title": "Test",
        "description": "Test desc",
        "project_type": "WGS",
        "internal_accession": "NFDP-PRJ-000001",
    }
    xml_str = build_bioproject_xml(project, center_name="NFDP")
    assert "NFDP-PRJ-000001" in xml_str


def test_build_biosample_xml_single():
    samples = [{
        "internal_accession": "NFDP-SAM-000001",
        "organism": "Camelus dromedarius",
        "tax_id": 9838,
        "collection_date": "2026-01-15",
        "geographic_location": "Saudi Arabia:Riyadh",
        "breed": "Arabian",
    }]
    xml_str = build_biosample_xml(samples, "livestock", center_name="NFDP")
    root = ET.fromstring(xml_str)
    assert root.tag == "BioSampleSet"
    bs = root.find("BioSample")
    assert bs is not None
    # Check organism
    org = bs.find(".//Organism")
    assert org is not None
    assert org.get("taxonomy_id") == "9838"
    assert org.find("OrganismName").text == "Camelus dromedarius"
    # Check attributes use NCBI field names
    attrs = {a.get("attribute_name"): a.text for a in bs.findall(".//Attribute")}
    assert "geo_loc_name" in attrs  # mapped from geographic_location
    assert attrs["geo_loc_name"] == "Saudi Arabia:Riyadh"
    assert "collection_date" in attrs


def test_build_biosample_xml_batch():
    samples = [
        {
            "internal_accession": f"NFDP-SAM-00000{i}",
            "organism": "Camelus dromedarius",
            "tax_id": 9838,
            "collection_date": "2026-01-15",
            "geographic_location": "Saudi Arabia:Riyadh",
        }
        for i in range(1, 4)
    ]
    xml_str = build_biosample_xml(samples, "livestock", center_name="NFDP")
    root = ET.fromstring(xml_str)
    assert len(root.findall("BioSample")) == 3


def test_build_sra_xml():
    experiments = [{
        "internal_accession": "NFDP-EXP-000001",
        "platform": "ILLUMINA",
        "instrument_model": "NovaSeq 6000",
        "library_strategy": "WGS",
        "library_source": "GENOMIC",
        "library_layout": "PAIRED",
        "sample_accession": "NFDP-SAM-000001",
    }]
    runs = [{
        "internal_accession": "NFDP-RUN-000001",
        "filename": "SAMPLE_001_R1.fastq.gz",
        "file_type": "fastq",
        "checksum_md5": "d41d8cd98f00b204e9800998ecf8427e",
        "experiment_accession": "NFDP-EXP-000001",
    }]
    xml_str = build_sra_xml(experiments, runs, center_name="NFDP")
    root = ET.fromstring(xml_str)
    assert root.find(".//Experiment") is not None
    assert root.find(".//Run") is not None
    file_elem = root.find(".//File")
    assert file_elem.get("filename") == "SAMPLE_001_R1.fastq.gz"
    assert file_elem.get("checksum") == "d41d8cd98f00b204e9800998ecf8427e"
