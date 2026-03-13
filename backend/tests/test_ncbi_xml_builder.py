import pytest
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
