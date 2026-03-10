from __future__ import annotations
from typing import Any


def _get_file_by_direction(runs: list[dict[str, Any]], direction: str) -> str:
    for r in runs:
        if r.get("direction") == direction:
            return r["file_path"]
    return ""


class GenericFormatter:
    columns = ["sample", "fastq_1", "fastq_2"]

    def map_rows(self, samples: list[dict[str, Any]], runs_by_sample: dict[str, list[dict[str, Any]]]) -> list[dict[str, str]]:
        rows = []
        for s in samples:
            acc = s["accession"]
            runs = runs_by_sample.get(acc, [])
            rows.append({
                "sample": acc,
                "fastq_1": _get_file_by_direction(runs, "forward"),
                "fastq_2": _get_file_by_direction(runs, "reverse"),
            })
        return rows
