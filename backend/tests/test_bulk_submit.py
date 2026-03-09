"""Tests for the bulk submit service."""

import pytest

from app.services.bulk_submit import BulkSubmitService, _detect_file_type


TSV_WITH_FILES = (
    "sample_alias\torganism\ttax_id\tcollection_date\tgeographic_location"
    "\tfilename_forward\tfilename_reverse\tmd5_forward\tmd5_reverse"
    "\tlibrary_strategy\tplatform\tinstrument_model\n"
    "SAMPLE_A\tOvis aries\t9940\t2026-01-15\tSaudi Arabia:Riyadh"
    "\tSAMPLE_A_R1.fastq.gz\tSAMPLE_A_R2.fastq.gz\tabc123\tdef456"
    "\tWGS\tILLUMINA\tNovaSeq 6000\n"
)

TSV_WITHOUT_FILES = (
    "sample_alias\torganism\ttax_id\tcollection_date\tgeographic_location"
    "\tlibrary_strategy\tplatform\tinstrument_model\n"
    "SAMPLE_B\tCapra hircus\t9925\t2026-02-01\tSaudi Arabia:Jeddah"
    "\tWGS\tILLUMINA\tNovaSeq 6000\n"
)

TSV_MISSING_FIELD = (
    "sample_alias\torganism\tcollection_date\tgeographic_location\n"
    "SAMPLE_C\tBos taurus\t2026-03-01\tSaudi Arabia:Tabuk\n"
)


class TestParseSampleSheet:
    def test_parse_sample_sheet_with_explicit_files(self):
        svc = BulkSubmitService.__new__(BulkSubmitService)
        rows = svc.parse_sample_sheet(TSV_WITH_FILES)
        assert len(rows) == 1
        assert rows[0]["sample_alias"] == "SAMPLE_A"
        assert rows[0]["filename_forward"] == "SAMPLE_A_R1.fastq.gz"
        assert rows[0]["filename_reverse"] == "SAMPLE_A_R2.fastq.gz"
        assert rows[0]["md5_forward"] == "abc123"
        assert rows[0]["md5_reverse"] == "def456"

    def test_parse_sample_sheet_without_file_columns(self):
        svc = BulkSubmitService.__new__(BulkSubmitService)
        rows = svc.parse_sample_sheet(TSV_WITHOUT_FILES)
        assert len(rows) == 1
        assert rows[0]["sample_alias"] == "SAMPLE_B"
        assert "filename_forward" not in rows[0]


class TestValidateRow:
    def test_validate_row_missing_required_field(self):
        svc = BulkSubmitService.__new__(BulkSubmitService)
        row = {"organism": "Bos taurus", "collection_date": "2026-03-01"}
        errors = svc.validate_row(row, 2, ["organism", "tax_id", "collection_date"])
        assert len(errors) == 1
        assert errors[0]["field"] == "tax_id"
        assert "missing" in errors[0]["message"].lower()

    def test_validate_row_all_present(self):
        svc = BulkSubmitService.__new__(BulkSubmitService)
        row = {"organism": "Bos taurus", "tax_id": "9913", "collection_date": "2026-03-01"}
        errors = svc.validate_row(row, 2, ["organism", "tax_id", "collection_date"])
        assert errors == []


class TestDetectFileType:
    def test_fastq(self):
        assert _detect_file_type("sample_R1.fastq.gz") == "FASTQ"

    def test_bam(self):
        assert _detect_file_type("aligned.bam") == "BAM"

    def test_cram(self):
        assert _detect_file_type("aligned.cram") == "CRAM"

    def test_vcf(self):
        assert _detect_file_type("variants.vcf.gz") == "VCF"

    def test_unknown(self):
        assert _detect_file_type("data.txt") == "OTHER"
