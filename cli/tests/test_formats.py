from seqdb_cli.formats import get_formatter, list_formats


def test_list_formats():
    fmts = list_formats()
    assert "generic" in fmts
    assert "rnaseq" in fmts
    assert "sarek" in fmts


def test_generic_format():
    fmt = get_formatter("generic")
    rows = fmt.map_rows(
        samples=[{
            "accession": "NFDP-SAM-000001",
            "external_id": None,
            "organism": "Bos taurus",
        }],
        runs_by_sample={
            "NFDP-SAM-000001": [
                {"file_path": "/data/s1_R1.fastq.gz", "direction": "forward"},
                {"file_path": "/data/s1_R2.fastq.gz", "direction": "reverse"},
            ]
        },
    )
    assert len(rows) == 1
    assert rows[0]["sample"] == "NFDP-SAM-000001"
    assert rows[0]["fastq_1"] == "/data/s1_R1.fastq.gz"
    assert rows[0]["fastq_2"] == "/data/s1_R2.fastq.gz"


def test_rnaseq_format():
    fmt = get_formatter("rnaseq")
    rows = fmt.map_rows(
        samples=[{"accession": "NFDP-SAM-000001", "external_id": None, "organism": "Bos taurus"}],
        runs_by_sample={
            "NFDP-SAM-000001": [
                {"file_path": "/data/s1_R1.fastq.gz", "direction": "forward"},
                {"file_path": "/data/s1_R2.fastq.gz", "direction": "reverse"},
            ]
        },
    )
    assert rows[0]["strandedness"] == "auto"
    assert "fastq_1" in rows[0]


def test_sarek_format():
    fmt = get_formatter("sarek")
    rows = fmt.map_rows(
        samples=[{
            "accession": "NFDP-SAM-000001",
            "external_id": "COW_001",
            "organism": "Bos taurus",
        }],
        runs_by_sample={
            "NFDP-SAM-000001": [
                {"file_path": "/data/s1_R1.fastq.gz", "direction": "forward"},
                {"file_path": "/data/s1_R2.fastq.gz", "direction": "reverse"},
            ]
        },
    )
    assert rows[0]["patient"] == "Bos taurus"
    assert rows[0]["sample"] == "NFDP-SAM-000001"
    assert rows[0]["lane"] == "lane_1"
