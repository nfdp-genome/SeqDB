import csv
import httpx
import pytest
import respx
from pathlib import Path
from seqdb_cli.commands.fetch import fetch as fetch_command, _resolve_accession
from seqdb_cli.config import SeqDBConfig
from seqdb_cli.client import SeqDBClient

SAMPLE_RESPONSE = {
    "accession": "NFDP-SAM-000001",
    "ena_accession": None,
    "organism": "Bos taurus",
    "tax_id": 9913,
    "breed": "Holstein",
    "collection_date": "2026-01-15",
    "geographic_location": "Canada",
    "checklist_id": "ERC000011",
    "created_at": "2026-01-01T00:00:00",
}

RUN_RESPONSES = [
    {
        "accession": "NFDP-RUN-000001",
        "file_type": "FASTQ",
        "file_size": 1000,
        "checksum_md5": "abc123",
        "file_path": "nfdp-raw/prj/sam/run/sample_R1.fastq.gz",
        "created_at": "2026-01-01T00:00:00",
    },
    {
        "accession": "NFDP-RUN-000002",
        "file_type": "FASTQ",
        "file_size": 1000,
        "checksum_md5": "def456",
        "file_path": "nfdp-raw/prj/sam/run/sample_R2.fastq.gz",
        "created_at": "2026-01-01T00:00:00",
    },
]


@respx.mock
@pytest.mark.asyncio
async def test_resolve_project_accession():
    cfg = SeqDBConfig(server_url="https://api.test", access_token="tok")
    client = SeqDBClient(cfg)

    respx.get("https://api.test/api/v1/projects/NFDP-PRJ-000001").mock(
        return_value=httpx.Response(200, json={"accession": "NFDP-PRJ-000001", "title": "Test"})
    )
    respx.get("https://api.test/api/v1/samples/").mock(
        return_value=httpx.Response(200, json=[SAMPLE_RESPONSE])
    )
    respx.get("https://api.test/api/v1/runs/").mock(
        return_value=httpx.Response(200, json=RUN_RESPONSES)
    )

    samples, runs_by_sample = await _resolve_accession(client, "NFDP-PRJ-000001")
    assert len(samples) == 1
    assert samples[0]["accession"] == "NFDP-SAM-000001"
    assert "NFDP-SAM-000001" in runs_by_sample
    assert len(runs_by_sample["NFDP-SAM-000001"]) == 2
    await client.close()
