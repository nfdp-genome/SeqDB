"""Parse NCBI Entrez-style query strings into structured tokens."""

import re
from dataclasses import dataclass


@dataclass
class QueryTerm:
    """A single parsed query term."""
    text: str = ""
    field: str | None = None
    operator: str | None = None
    date_from: str | None = None
    date_to: str | None = None


# Pattern for date range: YYYY/MM/DD:YYYY/MM/DD[FIELD]
_DATE_RANGE_RE = re.compile(
    r"(\d{4}/\d{2}/\d{2}):(\d{4}/\d{2}/\d{2})\[([A-Z]+)\]"
)

# Pattern for field-qualified term: text[FIELD]
_FIELD_QUAL_RE = re.compile(r"(.+?)\[([A-Z]+)\]")

# Boolean operators
_BOOLEAN_OPS = {"AND", "OR", "NOT"}


def parse_query(query: str) -> list[QueryTerm]:
    """Parse an Entrez-style query string into a list of QueryTerms.

    Supports:
    - Field-qualified: organism[ORGN], camel[TITL]
    - Boolean: AND, OR, NOT
    - Date range: 2026/01/01:2026/12/31[PDAT]
    - Plain text: camel WGS
    - Accession: NFDP-PRJ-000001
    """
    query = query.strip()
    if not query:
        return []

    tokens = []
    remaining = query

    while remaining:
        remaining = remaining.strip()
        if not remaining:
            break

        # Try date range first
        date_match = _DATE_RANGE_RE.match(remaining)
        if date_match:
            tokens.append(QueryTerm(
                text=date_match.group(0),
                field=date_match.group(3),
                date_from=date_match.group(1),
                date_to=date_match.group(2),
            ))
            remaining = remaining[date_match.end():]
            continue

        # Check for boolean operator at start
        for op in _BOOLEAN_OPS:
            if remaining.startswith(op + " "):
                tokens.append(QueryTerm(operator=op))
                remaining = remaining[len(op):]
                break
        else:
            # Try field-qualified term
            next_op_pos = len(remaining)
            for op in _BOOLEAN_OPS:
                pos = remaining.find(f" {op} ")
                if pos != -1 and pos < next_op_pos:
                    next_op_pos = pos

            chunk = remaining[:next_op_pos].strip()
            remaining = remaining[next_op_pos:]

            if chunk:
                field_match = _FIELD_QUAL_RE.match(chunk)
                if field_match:
                    tokens.append(QueryTerm(
                        text=field_match.group(1).strip(),
                        field=field_match.group(2),
                    ))
                else:
                    tokens.append(QueryTerm(text=chunk))

    return tokens
