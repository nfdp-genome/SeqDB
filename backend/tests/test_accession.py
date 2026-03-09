import pytest
from app.services.accession import generate_accession, validate_accession, AccessionType


def test_generate_accession_project():
    acc = generate_accession(AccessionType.PROJECT, 1)
    assert acc == "NFDP-PRJ-000001"


def test_generate_accession_sample():
    acc = generate_accession(AccessionType.SAMPLE, 42)
    assert acc == "NFDP-SAM-000042"


def test_generate_accession_experiment():
    acc = generate_accession(AccessionType.EXPERIMENT, 100)
    assert acc == "NFDP-EXP-000100"


def test_generate_accession_run():
    acc = generate_accession(AccessionType.RUN, 999999)
    assert acc == "NFDP-RUN-999999"


def test_generate_accession_submission():
    acc = generate_accession(AccessionType.SUBMISSION, 15)
    assert acc == "NFDP-SUB-000015"


def test_validate_accession_valid():
    assert validate_accession("NFDP-PRJ-000001") is True
    assert validate_accession("NFDP-SAM-123456") is True


def test_validate_accession_invalid():
    assert validate_accession("INVALID") is False
    assert validate_accession("NFDP-XXX-000001") is False
    assert validate_accession("NFDP-PRJ-1") is False
