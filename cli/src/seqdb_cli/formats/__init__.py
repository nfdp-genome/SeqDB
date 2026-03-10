from __future__ import annotations
from typing import Any, Protocol


class SamplesheetFormatter(Protocol):
    columns: list[str]
    def map_rows(self, samples: list[dict[str, Any]], runs_by_sample: dict[str, list[dict[str, Any]]]) -> list[dict[str, str]]: ...


def get_formatter(name: str) -> SamplesheetFormatter:
    formatters = _get_registry()
    if name not in formatters:
        raise ValueError(f"Unknown format '{name}'. Available: {list(formatters.keys())}")
    return formatters[name]()


def list_formats() -> list[str]:
    return list(_get_registry().keys())


def _get_registry() -> dict[str, type]:
    from seqdb_cli.formats.generic import GenericFormatter
    from seqdb_cli.formats.rnaseq import RnaseqFormatter
    from seqdb_cli.formats.sarek import SarekFormatter
    return {"generic": GenericFormatter, "rnaseq": RnaseqFormatter, "sarek": SarekFormatter}
