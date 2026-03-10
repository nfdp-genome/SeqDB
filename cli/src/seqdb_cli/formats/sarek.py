from __future__ import annotations
from typing import Any
from seqdb_cli.formats.generic import _get_file_by_direction


class SarekFormatter:
    columns = ["patient", "sample", "lane", "fastq_1", "fastq_2"]

    def map_rows(self, samples: list[dict[str, Any]], runs_by_sample: dict[str, list[dict[str, Any]]]) -> list[dict[str, str]]:
        rows = []
        for s in samples:
            acc = s["accession"]
            runs = runs_by_sample.get(acc, [])
            rows.append({
                "patient": s.get("organism") or s.get("external_id") or acc,
                "sample": acc,
                "lane": "lane_1",
                "fastq_1": _get_file_by_direction(runs, "forward"),
                "fastq_2": _get_file_by_direction(runs, "reverse"),
            })
        return rows
